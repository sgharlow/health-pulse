"""Tests for the quality_monitor tool."""

import pytest
from unittest.mock import patch

from healthpulse_mcp.tools.quality_monitor import run


ENV = {
    "HP_QUALITY_DATASET_ID": "quality-dataset-123",
    "HP_FACILITIES_DATASET_ID": "facilities-dataset-123",
}


@pytest.mark.asyncio
async def test_quality_monitor_returns_expected_structure(mock_domo, sample_quality_rows):
    """Tool returns required top-level keys."""
    mock_domo.query_as_dicts.return_value = sample_quality_rows

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure_group": "all", "threshold_sigma": 2.0})

    assert "total_facilities_analyzed" in result
    assert "measures_checked" in result
    assert "anomaly_count" in result
    assert "anomalies" in result
    assert "filters" in result


@pytest.mark.asyncio
async def test_quality_monitor_detects_outlier(mock_domo):
    """Outlier facility is detected when its score is far from the cluster."""
    # Use tightly clustered values so the outlier exceeds z=2.0 (matching analytics test pattern)
    rows = [
        {"facility_id": "A", "facility_name": "H-A", "state": "CA",
         "measure_id": "MORT_30_AMI", "score": "10.0"},
        {"facility_id": "B", "facility_name": "H-B", "state": "CA",
         "measure_id": "MORT_30_AMI", "score": "11.0"},
        {"facility_id": "C", "facility_name": "H-C", "state": "CA",
         "measure_id": "MORT_30_AMI", "score": "10.0"},
        {"facility_id": "D", "facility_name": "H-D", "state": "CA",
         "measure_id": "MORT_30_AMI", "score": "11.0"},
        {"facility_id": "E", "facility_name": "H-E", "state": "CA",
         "measure_id": "MORT_30_AMI", "score": "10.0"},
        {"facility_id": "F", "facility_name": "H-F", "state": "CA",
         "measure_id": "MORT_30_AMI", "score": "11.0"},
        {"facility_id": "OUTLIER", "facility_name": "Outlier Hospital", "state": "CA",
         "measure_id": "MORT_30_AMI", "score": "50.0"},
    ]
    mock_domo.query_as_dicts.return_value = rows

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure_group": "mortality", "threshold_sigma": 2.0})

    anomalies = result["anomalies"]
    outlier_ids = [a["facility_id"] for a in anomalies]
    assert "OUTLIER" in outlier_ids


@pytest.mark.asyncio
async def test_quality_monitor_filters_by_state(mock_domo, sample_quality_rows, sample_facilities_rows):
    """State filter queries facilities dataset first, then filters quality data in Python.

    Quality dataset has no 'state' column, so the state filter is applied by:
    1. Querying the facilities dataset for facility_ids in the given state.
    2. Filtering quality rows in Python using those facility_ids.
    """
    call_count = [0]

    def side_effect(dataset_id, sql):
        call_count[0] += 1
        if call_count[0] == 1:
            # First call: facilities query for state filter
            return sample_facilities_rows
        # Second call: quality query (all rows, filtered in Python)
        return sample_quality_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"state": "CA", "measure_group": "all"})

    assert result["filters"]["state"] == "CA"
    calls = mock_domo.query_as_dicts.call_args_list
    # First call (facilities) must include state = 'CA'
    assert "state = 'CA'" in calls[0][0][1]
    # Second call (quality) must NOT have state in SQL (it uses facility_id filter in Python)
    assert "state = 'CA'" not in calls[1][0][1]


@pytest.mark.asyncio
async def test_quality_monitor_measure_group_filter(mock_domo, sample_quality_rows):
    """measure_group=mortality only uses MORT_ prefixed measures."""
    mock_domo.query_as_dicts.return_value = sample_quality_rows

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure_group": "mortality"})

    # Only MORT_ rows should be analyzed: 5 rows across 5 facilities
    assert result["total_facilities_analyzed"] == 5
    assert result["filters"]["measure_group"] == "mortality"


@pytest.mark.asyncio
async def test_quality_monitor_anomalies_capped_at_20(mock_domo):
    """Anomalies list is capped at 20 items even with many outliers."""
    # Generate 25 rows with varied scores to trigger many anomalies
    rows = [
        {"facility_id": str(i), "facility_name": f"H{i}", "state": "TX",
         "measure_id": "MORT_30_AMI", "score": str(float(i * 5))}
        for i in range(1, 26)
    ]
    mock_domo.query_as_dicts.return_value = rows

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure_group": "all", "threshold_sigma": 1.0})

    assert len(result["anomalies"]) <= 20


@pytest.mark.asyncio
async def test_quality_monitor_missing_dataset_id(mock_domo):
    """Returns error dict when dataset ID env var is not set."""
    with patch.dict("os.environ", {}, clear=True):
        result = await run(mock_domo, {"measure_group": "all"})

    assert "error" in result
    assert "HP_QUALITY_DATASET_ID" in result["error"]


@pytest.mark.asyncio
async def test_quality_monitor_empty_data(mock_domo):
    """Handles empty dataset gracefully."""
    mock_domo.query_as_dicts.return_value = []

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure_group": "all"})

    assert result["total_facilities_analyzed"] == 0
    assert result["anomaly_count"] == 0
    assert result["anomalies"] == []


@pytest.mark.asyncio
async def test_quality_monitor_threshold_sigma_respected(mock_domo, sample_quality_rows):
    """High threshold_sigma reduces anomaly count."""
    mock_domo.query_as_dicts.return_value = sample_quality_rows

    with patch.dict("os.environ", ENV):
        result_low = await run(mock_domo, {"measure_group": "mortality", "threshold_sigma": 1.5})
        result_high = await run(mock_domo, {"measure_group": "mortality", "threshold_sigma": 3.5})

    # Lower threshold should find at least as many anomalies as higher threshold
    assert result_low["anomaly_count"] >= result_high["anomaly_count"]
