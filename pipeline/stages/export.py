"""Stage 6: Export — FAISS index, representative quotes, enriched GeoJSON."""
from __future__ import annotations

import collections
import datetime
import glob
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


_ANSI = {"WARN": "\033[93m", "FAIL": "\033[91m", "INFO": ""}
_RESET = "\033[0m"


def _log(level: str, msg: str) -> None:
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
    color = _ANSI.get(level, "") if sys.stdout.isatty() else ""
    reset = _RESET if color else ""
    print(f"{color}[{level}] {ts}  {msg}{reset}", flush=True)


# ---------------------------------------------------------------------------
# Expected artifacts for final validation (NLP-09)
# ---------------------------------------------------------------------------

EXPECTED_ARTIFACTS = [
    "embeddings.npy",
    "review_ids.npy",
    "bertopic_model",
    "topic_assignments.json",
    "vibe_scores.json",
    "temporal_series.json",
    "faiss_index.bin",
    "faiss_id_map.json",
    "representative_quotes.json",
    "sentiment_model",
    "neighbourhood_sentiment.json",
    "enriched_geojson.geojson",
    "neighbourhood_topics.json",
    "review_counts.json",
]


# ---------------------------------------------------------------------------
# Sub-stage A: FAISS Index (NLP-07)
# ---------------------------------------------------------------------------

def _build_faiss_index(
    vibe_scores: dict[str, dict[str, float]],
    artifacts_dir: Path,
) -> "faiss.IndexFlatIP":
    """Build FAISS flat index over L2-normalized 6D vibe vectors.

    Args:
        vibe_scores: {neighbourhood_id: {archetype: score}}
        artifacts_dir: output directory

    Returns:
        The built FAISS index.
    """
    import faiss

    archetype_order = ["artsy", "foodie", "nightlife", "family", "upscale", "cultural"]
    sorted_nids = sorted(vibe_scores.keys())

    vibe_matrix = np.array(
        [[vibe_scores[nid][a] for a in archetype_order] for nid in sorted_nids],
        dtype=np.float32,
    )

    faiss.normalize_L2(vibe_matrix)  # in-place L2 normalization for cosine similarity
    index = faiss.IndexFlatIP(6)  # 6 vibe dimensions, inner product
    index.add(vibe_matrix)
    faiss.write_index(index, str(artifacts_dir / "faiss_index.bin"))
    _log("INFO", f"FAISS index built: {index.ntotal} vectors, dim={index.d}")

    # Save ID map: integer index -> neighbourhood_id
    faiss_id_map = {i: nid for i, nid in enumerate(sorted_nids)}
    with open(artifacts_dir / "faiss_id_map.json", "w") as f:
        json.dump(faiss_id_map, f, indent=2)
    _log("INFO", f"FAISS ID map saved: {len(faiss_id_map)} entries")

    return index


# ---------------------------------------------------------------------------
# Sub-stage B: Representative Quotes (NLP-08)
# ---------------------------------------------------------------------------

def _select_representative_quotes(
    db_path: str,
    artifacts_dir: Path,
    vibe_scores: dict[str, dict[str, float]],
) -> dict:
    """Select 3-5 representative quotes per neighbourhood per archetype.

    Quotes are ranked by cosine similarity of the review embedding
    to the archetype centroid embedding. Truncated to 300 chars max.

    Returns:
        {neighbourhood_id: {archetype: [quote_text, ...]}}
    """
    from sentence_transformers import SentenceTransformer

    # Load embeddings and review IDs
    embeddings = np.load(artifacts_dir / "embeddings.npy")
    review_ids = np.load(artifacts_dir / "review_ids.npy")

    # Load archetype seed phrases and compute centroids
    archetypes_path = Path(__file__).parent.parent / "archetypes.json"
    with open(archetypes_path) as f:
        archetypes = json.load(f)

    model = SentenceTransformer("all-MiniLM-L6-v2")
    archetype_centroids: dict[str, np.ndarray] = {}
    for name, phrases in archetypes.items():
        phrase_embs = model.encode(phrases)
        archetype_centroids[name] = phrase_embs.mean(axis=0)

    _log("INFO", f"Computed {len(archetype_centroids)} archetype centroids for quote selection")

    # Load review texts and neighbourhood mappings from DB
    conn = sqlite3.connect(db_path)
    review_data: dict[int, tuple[str, str]] = {}  # {rowid: (text, neighbourhood_id)}
    for row in conn.execute("""
        SELECT r.rowid, r.text, b.neighbourhood_id
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE b.neighbourhood_id IS NOT NULL
    """):
        review_data[row[0]] = (row[1], row[2])
    conn.close()

    _log("INFO", f"Loaded {len(review_data)} reviews for quote selection")

    # Build index: review_ids entry -> position in embeddings array
    rid_to_idx: dict[int, int] = {}
    for idx, rid in enumerate(review_ids):
        rid_to_idx[int(rid)] = idx

    sorted_nids = sorted(vibe_scores.keys())
    quotes: dict[str, dict[str, list[str]]] = {}

    for nid in sorted_nids:
        quotes[nid] = {}

        # Get embedding indices for reviews in this neighbourhood
        nid_indices = []
        nid_rids = []
        for rid, (text, rid_nid) in review_data.items():
            if rid_nid == nid and rid in rid_to_idx:
                nid_indices.append(rid_to_idx[rid])
                nid_rids.append(rid)

        if not nid_indices:
            for arch_name in archetypes:
                quotes[nid][arch_name] = []
            continue

        nid_embeddings = embeddings[nid_indices]

        for arch_name, arch_centroid in archetype_centroids.items():
            sims = cosine_similarity(
                nid_embeddings, arch_centroid.reshape(1, -1)
            ).flatten()
            top_k = min(5, len(sims))
            top_indices = np.argsort(sims)[-top_k:][::-1]  # descending similarity

            arch_quotes = []
            for ti in top_indices:
                rid = nid_rids[ti]
                text = review_data[rid][0]
                # Truncate to 300 chars
                if len(text) > 300:
                    text = text[:297] + "..."
                arch_quotes.append(text)

            quotes[nid][arch_name] = arch_quotes

    # Save
    with open(artifacts_dir / "representative_quotes.json", "w") as f:
        json.dump(quotes, f, indent=2)

    _log("INFO", f"Representative quotes saved: {len(quotes)} neighbourhoods")
    return quotes


# ---------------------------------------------------------------------------
# Sub-stage C: Enriched GeoJSON (NLP-09 partial)
# ---------------------------------------------------------------------------

def _build_enriched_geojson(
    vibe_scores: dict[str, dict[str, float]],
    artifacts_dir: Path,
    geojson_path: str | None = None,
) -> None:
    """Inject vibe scores into GeoJSON feature properties.

    Searches for the Philadelphia boundaries GeoJSON file and enriches
    each feature whose NEIGHBORHOOD_NUMBER matches a vibe_scores key.
    """
    # Find GeoJSON boundaries file
    if geojson_path is None:
        candidates = (
            glob.glob("scripts/data/boundaries/*.geojson")
            + glob.glob("data/boundaries/*.geojson")
        )
        if not candidates:
            _log("WARN", "No boundaries GeoJSON found -- skipping enriched GeoJSON")
            return
        geojson_path = candidates[0]

    _log("INFO", f"Loading boundaries GeoJSON from {geojson_path}")
    with open(geojson_path) as f:
        geojson = json.load(f)

    # Load neighbourhood sentiment if available
    sentiment_path = artifacts_dir / "neighbourhood_sentiment.json"
    neighbourhood_sentiment: dict = {}
    if sentiment_path.exists():
        with open(sentiment_path) as f:
            neighbourhood_sentiment = json.load(f)
        _log("INFO", f"Loaded sentiment for {len(neighbourhood_sentiment)} neighbourhoods")

    enriched_count = 0
    for feature in geojson["features"]:
        nid = feature["properties"].get("NEIGHBORHOOD_NUMBER")
        if nid and nid in vibe_scores:
            scores = vibe_scores[nid]
            feature["properties"]["vibe_scores"] = scores
            dominant = max(scores, key=scores.get)
            feature["properties"]["dominant_vibe"] = dominant
            feature["properties"]["dominant_vibe_score"] = scores[dominant]
            if nid in neighbourhood_sentiment:
                feature["properties"]["sentiment"] = neighbourhood_sentiment[nid]
            enriched_count += 1

    with open(artifacts_dir / "enriched_geojson.geojson", "w") as f:
        json.dump(geojson, f, indent=2)

    _log("INFO", f"Enriched GeoJSON saved: {enriched_count}/{len(geojson['features'])} features enriched")


# ---------------------------------------------------------------------------
# Sub-stage D: Neighbourhood Topics (API-02)
# ---------------------------------------------------------------------------

def _build_neighbourhood_topics(db_path: str, artifacts_dir: Path) -> dict:
    """Build per-neighbourhood topic distributions from topic assignments.

    Returns:
        {neighbourhood_id: [{label, keywords, review_share}, ...]}
    """
    from bertopic import BERTopic

    # Load topic assignments: {review_rowid_str: topic_id}
    with open(artifacts_dir / "topic_assignments.json") as f:
        topic_assignments = json.load(f)

    # Load BERTopic model for topic representations
    topic_model = BERTopic.load(str(artifacts_dir / "bertopic_model"))

    # Build review-to-neighbourhood mapping from DB
    conn = sqlite3.connect(db_path)
    review_to_nid: dict[str, str] = {}
    for row in conn.execute(
        """
        SELECT r.rowid, b.neighbourhood_id
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE b.neighbourhood_id IS NOT NULL
        """
    ):
        review_to_nid[str(row[0])] = row[1]
    conn.close()

    # Count topic occurrences per neighbourhood
    nid_topic_counts: dict[str, collections.Counter] = {}
    nid_total_reviews: dict[str, int] = collections.defaultdict(int)

    for rowid_str, topic_id in topic_assignments.items():
        if topic_id == -1:  # skip outlier topics
            continue
        nid = review_to_nid.get(rowid_str)
        if nid is None:
            continue
        if nid not in nid_topic_counts:
            nid_topic_counts[nid] = collections.Counter()
        nid_topic_counts[nid][topic_id] += 1
        nid_total_reviews[nid] += 1

    # Build result: top 10 topics per neighbourhood with labels and keywords
    result: dict[str, list[dict]] = {}
    for nid, counter in sorted(nid_topic_counts.items()):
        top_topics = counter.most_common(10)
        total = nid_total_reviews[nid]
        entries = []
        for topic_id, count in top_topics:
            rep = topic_model.get_topic(topic_id)
            if not rep or rep is False:
                continue
            label = " ".join([w for w, _ in rep[:3]])
            keywords = [w for w, _ in rep[:5]]
            entries.append({
                "label": label,
                "keywords": keywords,
                "review_share": round(count / total, 4),
            })
        result[nid] = entries

    with open(artifacts_dir / "neighbourhood_topics.json", "w") as f:
        json.dump(result, f, indent=2)

    _log("INFO", f"Neighbourhood topics saved: {len(result)} neighbourhoods")
    return result


# ---------------------------------------------------------------------------
# Sub-stage E: Review Counts (API-02)
# ---------------------------------------------------------------------------

def _build_review_counts(db_path: str, artifacts_dir: Path) -> dict:
    """Build per-neighbourhood review counts.

    Returns:
        {neighbourhood_id: count}
    """
    conn = sqlite3.connect(db_path)
    counts: dict[str, int] = {}
    for row in conn.execute(
        """
        SELECT b.neighbourhood_id, COUNT(*)
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE b.neighbourhood_id IS NOT NULL
        GROUP BY b.neighbourhood_id
        """
    ):
        counts[row[0]] = row[1]
    conn.close()

    with open(artifacts_dir / "review_counts.json", "w") as f:
        json.dump(counts, f, indent=2)

    _log("INFO", f"Review counts saved: {len(counts)} neighbourhoods")
    return counts


# ---------------------------------------------------------------------------
# Main stage entry point
# ---------------------------------------------------------------------------

def run_export(
    db_path: str,
    artifacts_dir: Path,
    force: bool = False,
    geojson_path: str | None = None,
) -> dict:
    """Build FAISS index, select representative quotes, export enriched GeoJSON.

    Outputs:
        artifacts_dir / faiss_index.bin
        artifacts_dir / faiss_id_map.json
        artifacts_dir / representative_quotes.json
        artifacts_dir / enriched_geojson.geojson
    """
    output_path = artifacts_dir / "enriched_geojson.geojson"
    if output_path.exists() and not force:
        _log("INFO", f"Stage 'export': artifact exists at {output_path}, skipping")
        return {"skipped": True}

    _log("INFO", "Stage 'export': starting...")

    # Load vibe scores (input from vibe_score stage)
    with open(artifacts_dir / "vibe_scores.json") as f:
        vibe_scores = json.load(f)
    _log("INFO", f"Loaded vibe scores for {len(vibe_scores)} neighbourhoods")

    # Sub-stage A: FAISS Index (NLP-07)
    index = _build_faiss_index(vibe_scores, artifacts_dir)

    # Sub-stage B: Representative Quotes (NLP-08)
    quotes = _select_representative_quotes(db_path, artifacts_dir, vibe_scores)

    # Sub-stage C: Enriched GeoJSON (NLP-09 partial)
    _build_enriched_geojson(vibe_scores, artifacts_dir, geojson_path)

    # Sub-stage D: Neighbourhood Topics (API-02)
    topics = _build_neighbourhood_topics(db_path, artifacts_dir)

    # Sub-stage E: Review Counts (API-02)
    counts = _build_review_counts(db_path, artifacts_dir)

    # Final artifact validation (NLP-09)
    missing = [a for a in EXPECTED_ARTIFACTS if not (artifacts_dir / a).exists()]
    if missing:
        _log("WARN", f"Missing artifacts: {missing}")
    else:
        _log("INFO", f"All {len(EXPECTED_ARTIFACTS)} artifacts present -- pipeline complete")

    _log("INFO", "Stage 'export': complete")

    return {
        "skipped": False,
        "faiss_ntotal": index.ntotal,
        "quote_neighbourhoods": len(quotes),
        "topic_neighbourhoods": len(topics),
        "review_count_neighbourhoods": len(counts),
        "missing_artifacts": missing,
    }
