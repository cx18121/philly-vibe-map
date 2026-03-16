"""Smoke tests for scripts/00_probe_coverage.py -- DATA-01."""
import pytest


def _load_probe():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "probe_module", "scripts/00_probe_coverage.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def probe_module():
    return _load_probe()


def test_probe_returns_correct_count(probe_module, sample_business_ndjson):
    result = probe_module.probe_coverage(sample_business_ndjson)
    assert result["total_businesses"] == 3
    assert result["nyc_bbox_businesses"] == 2
    assert result["missing_coords"] == 0
    assert result["nyc_pct"] == pytest.approx(66.67, abs=0.1)


def test_probe_handles_missing_coords(probe_module, sample_business_ndjson_missing_coords):
    result = probe_module.probe_coverage(sample_business_ndjson_missing_coords)
    assert result["total_businesses"] == 1
    assert result["missing_coords"] == 1
    assert result["nyc_bbox_businesses"] == 0


def test_probe_raises_on_missing_file(probe_module):
    with pytest.raises(FileNotFoundError):
        probe_module.probe_coverage("/nonexistent/path/business.json")


def test_probe_result_keys(probe_module, sample_business_ndjson):
    result = probe_module.probe_coverage(sample_business_ndjson)
    assert set(result.keys()) == {"total_businesses", "nyc_bbox_businesses", "missing_coords", "nyc_pct"}
