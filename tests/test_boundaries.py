"""Unit tests for Philadelphia neighbourhood boundary download -- DATA-04.

Project pivoted from NYC to Philadelphia (see .planning/phases/01-data-foundation/01-01-DECISION.md).
Boundary source: OpenDataPhilly ArcGIS FeatureServer.
Key fields: NEIGHBORHOOD_NUMBER (unique ID), NEIGHBORHOOD_NAME (display name).
"""


def test_neighborhood_number_unique(sample_nta_gdf):
    """NEIGHBORHOOD_NUMBER values must be unique -- used as neighbourhood_id in database."""
    numbers = sample_nta_gdf["NEIGHBORHOOD_NUMBER"].tolist()
    assert len(numbers) == len(set(numbers)), "Duplicate NEIGHBORHOOD_NUMBER values found"


def test_crs_is_wgs84(sample_nta_gdf):
    """GeoDataFrame CRS must be EPSG:4326 before spatial join."""
    assert sample_nta_gdf.crs is not None
    assert sample_nta_gdf.crs.to_epsg() == 4326


def test_neighborhood_has_required_columns(sample_nta_gdf):
    """GeoDataFrame must have NEIGHBORHOOD_NUMBER and NEIGHBORHOOD_NAME columns."""
    for col in ("NEIGHBORHOOD_NUMBER", "NEIGHBORHOOD_NAME"):
        assert col in sample_nta_gdf.columns, f"Missing column: {col}"


def test_neighborhood_number_is_string(sample_nta_gdf):
    """NEIGHBORHOOD_NUMBER values are strings (e.g., '001', '044') for consistent key handling."""
    # Newer pandas uses StringDtype; older uses object. Both are string-compatible.
    dtype_name = str(sample_nta_gdf["NEIGHBORHOOD_NUMBER"].dtype).lower()
    assert "str" in dtype_name or sample_nta_gdf["NEIGHBORHOOD_NUMBER"].dtype == object, (
        f"Expected string dtype, got {sample_nta_gdf['NEIGHBORHOOD_NUMBER'].dtype}"
    )


def test_neighborhood_names_non_empty(sample_nta_gdf):
    """All NEIGHBORHOOD_NAME values must be non-empty strings."""
    for name in sample_nta_gdf["NEIGHBORHOOD_NAME"].tolist():
        assert isinstance(name, str) and name.strip(), f"Empty or null NEIGHBORHOOD_NAME: {name!r}"
