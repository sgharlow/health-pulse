"""Tests for the equity_detector tool."""

import pytest
from unittest.mock import patch

from healthpulse_mcp.tools.equity_detector import run


ENV = {
    "HP_COMMUNITY_DATASET_ID": "community-dataset-123",
    "HP_FACILITIES_DATASET_ID": "facilities-dataset-123",
}


@pytest.mark.asyncio
async def test_equity_detector_returns_expected_structure(
    mock_domo, sample_svi_rows, sample_facilities_rows
):
    """Tool returns required top-level keys."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_svi_rows
        return sample_facilities_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"svi_threshold": 0.75, "outcome_measure": "readmission"})

    assert "equity_flags" in result
    assert "disparity_summary" in result
    assert "filters" in result


@pytest.mark.asyncio
async def test_equity_detector_flags_high_svi_facilities(
    mock_domo, sample_svi_rows, sample_facilities_rows
):
    """Facilities in high-SVI counties (>= 0.75) are flagged."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_svi_rows
        return sample_facilities_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"svi_threshold": 0.75, "outcome_measure": "readmission"})

    # SVI scores: LA=0.82 (high), SF=0.45 (low), Fresno=0.91 (high)
    # Facilities: 100001 (LA, high), 100002 (SF, low), 100003 (Fresno, high)
    equity_flag_ids = [f["facility_id"] for f in result["equity_flags"]]
    assert "100001" in equity_flag_ids
    assert "100003" in equity_flag_ids
    assert "100002" not in equity_flag_ids


@pytest.mark.asyncio
async def test_equity_detector_disparity_summary_structure(
    mock_domo, sample_svi_rows, sample_facilities_rows
):
    """Disparity summary contains expected keys."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_svi_rows
        return sample_facilities_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"svi_threshold": 0.75})

    summary = result["disparity_summary"]
    assert "high_svi_facility_count" in summary
    assert "low_svi_facility_count" in summary
    assert "avg_star_rating_high_svi" in summary
    assert "avg_star_rating_low_svi" in summary
    assert "rating_gap" in summary


@pytest.mark.asyncio
async def test_equity_detector_rating_gap_computed_correctly(
    mock_domo, sample_svi_rows, sample_facilities_rows
):
    """Rating gap is low_svi_avg - high_svi_avg."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_svi_rows
        return sample_facilities_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"svi_threshold": 0.75})

    summary = result["disparity_summary"]
    # high_svi: facilities 100001 (rating=4) and 100003 (rating=2), avg=3.0
    # low_svi: facility 100002 (rating=3), avg=3.0
    assert summary["avg_star_rating_high_svi"] == 3.0
    assert summary["avg_star_rating_low_svi"] == 3.0
    assert summary["rating_gap"] == 0.0


@pytest.mark.asyncio
async def test_equity_detector_flags_sorted_by_svi(
    mock_domo, sample_svi_rows, sample_facilities_rows
):
    """Equity flags are sorted by SVI score descending."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_svi_rows
        return sample_facilities_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"svi_threshold": 0.75})

    svi_scores = [f["svi_score"] for f in result["equity_flags"]]
    assert svi_scores == sorted(svi_scores, reverse=True)


@pytest.mark.asyncio
async def test_equity_detector_equity_flags_capped_at_20(mock_domo):
    """Equity flags list is capped at 20."""
    # 25 high-SVI counties and 25 matching facilities
    svi_rows = [
        {"county_fips": str(i).zfill(5), "county_name": f"County{i}", "state": "TX",
         "svi_score": "0.9"}
        for i in range(1, 26)
    ]
    fac_rows = [
        {"facility_id": str(i), "facility_name": f"H{i}", "state": "TX",
         "county_fips": str(i).zfill(5), "overall_rating": "3", "hospital_type": "Acute Care"}
        for i in range(1, 26)
    ]
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return svi_rows
        return fac_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"svi_threshold": 0.75})

    assert len(result["equity_flags"]) == 20


@pytest.mark.asyncio
async def test_equity_detector_missing_community_id(mock_domo):
    """Returns error when HP_COMMUNITY_DATASET_ID is not set."""
    with patch.dict("os.environ", {"HP_FACILITIES_DATASET_ID": "f123"}, clear=True):
        result = await run(mock_domo, {})

    assert "error" in result
    assert "HP_COMMUNITY_DATASET_ID" in result["error"]


@pytest.mark.asyncio
async def test_equity_detector_missing_facilities_id(mock_domo):
    """Returns error when HP_FACILITIES_DATASET_ID is not set."""
    with patch.dict("os.environ", {"HP_COMMUNITY_DATASET_ID": "c123"}, clear=True):
        result = await run(mock_domo, {})

    assert "error" in result
    assert "HP_FACILITIES_DATASET_ID" in result["error"]


@pytest.mark.asyncio
async def test_equity_detector_state_filter(mock_domo, sample_svi_rows, sample_facilities_rows):
    """State filter is applied to both queries."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_svi_rows
        return sample_facilities_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"state": "CA", "svi_threshold": 0.75})

    assert result["filters"]["state"] == "CA"
    # Both calls should include the state condition
    calls = mock_domo.query_as_dicts.call_args_list
    for c in calls:
        assert "state = 'CA'" in c[0][1]
