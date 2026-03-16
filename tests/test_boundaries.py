"""Unit tests for NTA boundary download and borough filter -- DATA-04."""


def test_nta_borough_filter(sample_nta_gdf):
    """Filter NTA GeoDataFrame to Manhattan (1) and Brooklyn (3) -- Bronx (2) excluded."""
    filtered = sample_nta_gdf[sample_nta_gdf["BoroCode"].isin(["1", "3"])].copy()
    assert len(filtered) == 2
    assert set(filtered["BoroCode"].tolist()) == {"1", "3"}
    assert "2" not in filtered["BoroCode"].tolist()


def test_crs_is_wgs84(sample_nta_gdf):
    """NTA GeoDataFrame CRS must be EPSG:4326 before spatial join."""
    assert sample_nta_gdf.crs is not None
    assert sample_nta_gdf.crs.to_epsg() == 4326


def test_nta_has_required_columns(sample_nta_gdf):
    """NTA GeoDataFrame must have NTACode, NTAName, BoroCode columns."""
    for col in ("NTACode", "NTAName", "BoroCode"):
        assert col in sample_nta_gdf.columns, f"Missing column: {col}"


def test_nta_borocode_is_string(sample_nta_gdf):
    """BoroCode values are strings (Socrata serialises as str, not int) -- filter uses isin(['1','3'])."""
    # Newer pandas uses StringDtype; older uses object. Both are string-compatible.
    dtype_name = str(sample_nta_gdf["BoroCode"].dtype).lower()
    assert "str" in dtype_name or sample_nta_gdf["BoroCode"].dtype == object, (
        f"Expected string dtype, got {sample_nta_gdf['BoroCode'].dtype}"
    )
