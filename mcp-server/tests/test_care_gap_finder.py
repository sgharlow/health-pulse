"""Tests for the care_gap_finder tool."""

import pytest
from unittest.mock import patch, call

from healthpulse_mcp.tools.care_gap_finder import run


READM_ENV = {
    "HP_READMISSIONS_DATASET_ID": "readm-dataset-123",
    "HP_QUALITY_DATASET_ID": "quality-dataset-123",
}


@pytest.mark.asyncio
async def test_care_gap_finder_returns_expected_structure(mock_domo, sample_readmission_rows):
    """Tool returns required top-level keys."""
    mock_domo.query_as_dicts.return_value = sample_readmission_rows

    with patch.dict("os.environ", READM_ENV):
        result = await run(mock_domo, {"gap_type": "readmission", "min_excess_ratio": 1.05})

    assert "gaps" in result
    assert "total_gaps" in result
    assert "filters" in result


@pytest.mark.asyncio
async def test_care_gap_finder_readmission_gap_type(mock_domo, sample_readmission_rows):
    """gap_type=readmission only queries readmissions dataset."""
    mock_domo.query_as_dicts.return_value = sample_readmission_rows

    with patch.dict("os.environ", READM_ENV):
        result = await run(mock_domo, {"gap_type": "readmission", "min_excess_ratio": 1.05})

    # Two rows above 1.05: 100002 (1.15) and 100003 (1.08)
    assert result["total_gaps"] == 2
    gap_ids = [g["facility_id"] for g in result["gaps"]]
    assert "100002" in gap_ids
    assert "100003" in gap_ids
    assert "100001" not in gap_ids  # ratio 1.02 < 1.05


@pytest.mark.asyncio
async def test_care_gap_finder_sorts_by_excess_ratio(mock_domo, sample_readmission_rows):
    """Gaps are sorted by excess_ratio descending."""
    mock_domo.query_as_dicts.return_value = sample_readmission_rows

    with patch.dict("os.environ", READM_ENV):
        result = await run(mock_domo, {"gap_type": "readmission", "min_excess_ratio": 1.0})

    ratios = [g["excess_ratio"] for g in result["gaps"]]
    assert ratios == sorted(ratios, reverse=True)


@pytest.mark.asyncio
async def test_care_gap_finder_quality_worse_than_national(mock_domo, sample_quality_rows):
    """gap_type=mortality finds 'Worse Than the National Rate' quality records."""
    mock_domo.query_as_dicts.return_value = sample_quality_rows

    with patch.dict("os.environ", READM_ENV):
        result = await run(mock_domo, {"gap_type": "mortality", "min_excess_ratio": 1.0})

    # sample_quality_rows has one row with "Worse Than the National Rate"
    worse = [g for g in result["gaps"] if g.get("gap_type") == "worse_than_national"]
    assert len(worse) >= 1


@pytest.mark.asyncio
async def test_care_gap_finder_state_filter(mock_domo, sample_readmission_rows):
    """State filter is included in the query SQL."""
    mock_domo.query_as_dicts.return_value = sample_readmission_rows

    with patch.dict("os.environ", READM_ENV):
        result = await run(mock_domo, {"gap_type": "readmission", "state": "TX"})

    assert result["filters"]["state"] == "TX"
    call_sql = mock_domo.query_as_dicts.call_args[0][1]
    assert "state = 'TX'" in call_sql


@pytest.mark.asyncio
async def test_care_gap_finder_gaps_capped_at_30(mock_domo):
    """Gaps list is capped at 30 items."""
    rows = [
        {
            "facility_id": str(i),
            "facility_name": f"H{i}",
            "state": "FL",
            "measure_id": "READM_30_AMI",
            "excess_readmission_ratio": str(1.1 + i * 0.01),
            "number_of_readmissions": "50",
            "predicted_readmission_rate": "18.0",
        }
        for i in range(1, 41)
    ]
    mock_domo.query_as_dicts.return_value = rows

    with patch.dict("os.environ", READM_ENV):
        result = await run(mock_domo, {"gap_type": "readmission", "min_excess_ratio": 1.0})

    assert len(result["gaps"]) == 30
    assert result["total_gaps"] == 40


@pytest.mark.asyncio
async def test_care_gap_finder_missing_readmissions_id(mock_domo):
    """Returns error when HP_READMISSIONS_DATASET_ID is not set."""
    with patch.dict("os.environ", {"HP_QUALITY_DATASET_ID": "q123"}, clear=True):
        result = await run(mock_domo, {"gap_type": "readmission"})

    assert "error" in result


@pytest.mark.asyncio
async def test_care_gap_finder_missing_quality_id(mock_domo):
    """Returns error when HP_QUALITY_DATASET_ID is not set for quality gap types."""
    with patch.dict("os.environ", {"HP_READMISSIONS_DATASET_ID": "r123"}, clear=True):
        result = await run(mock_domo, {"gap_type": "mortality"})

    assert "error" in result


@pytest.mark.asyncio
async def test_care_gap_finder_all_gap_type(mock_domo, sample_readmission_rows, sample_quality_rows):
    """gap_type=all queries both datasets."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_readmission_rows
        return sample_quality_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", READM_ENV):
        result = await run(mock_domo, {"gap_type": "all", "min_excess_ratio": 1.0})

    assert call_count == 2
    assert "gaps" in result
