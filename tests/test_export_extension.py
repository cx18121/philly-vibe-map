"""Tests for export stage extensions: neighbourhood_topics.json and review_counts.json."""
import json
from pathlib import Path

import pytest

ARTIFACTS_DIR = Path("data/output/artifacts")


@pytest.mark.slow
def test_neighbourhood_topics_structure():
    """Verify neighbourhood_topics.json has correct structure."""
    path = ARTIFACTS_DIR / "neighbourhood_topics.json"
    assert path.exists(), f"Missing artifact: {path}"

    with open(path) as f:
        topics = json.load(f)

    assert isinstance(topics, dict), "Expected top-level dict"
    assert len(topics) >= 150, f"Expected 150+ neighbourhoods, got {len(topics)}"

    for nid, entries in topics.items():
        assert isinstance(nid, str), f"Key {nid!r} should be a string"
        assert isinstance(entries, list), f"Value for {nid} should be a list"
        assert len(entries) <= 10, f"Neighbourhood {nid} has {len(entries)} topics (max 10)"

        share_sum = 0.0
        for entry in entries:
            assert "label" in entry, f"Missing 'label' in topic entry for {nid}"
            assert "keywords" in entry, f"Missing 'keywords' in topic entry for {nid}"
            assert "review_share" in entry, f"Missing 'review_share' in topic entry for {nid}"
            assert isinstance(entry["label"], str)
            assert isinstance(entry["keywords"], list)
            assert isinstance(entry["review_share"], (int, float))
            share_sum += entry["review_share"]

        assert share_sum <= 1.0 + 1e-6, (
            f"Neighbourhood {nid} review_share sum {share_sum:.4f} exceeds 1.0"
        )


@pytest.mark.slow
def test_review_counts_structure():
    """Verify review_counts.json has correct structure."""
    path = ARTIFACTS_DIR / "review_counts.json"
    assert path.exists(), f"Missing artifact: {path}"

    with open(path) as f:
        counts = json.load(f)

    assert isinstance(counts, dict), "Expected top-level dict"
    assert len(counts) >= 150, f"Expected 150+ neighbourhoods, got {len(counts)}"

    for nid, count in counts.items():
        assert isinstance(nid, str), f"Key {nid!r} should be a string"
        assert isinstance(count, int), f"Value for {nid} should be an int, got {type(count)}"
        assert count > 0, f"Neighbourhood {nid} has count {count}, expected > 0"
