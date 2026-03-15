"""Tests for the state_ranking tool."""

import pytest
from unittest.mock import patch

from healthpulse_mcp.tools.state_ranking import run


ENV = {
    "HP_FACILITIES_DATASET_ID": "facilities-dataset-123",
    "HP_QUALITY_DATASET_ID": "quality-dataset-123",
}

# Sample aggregated facility rows (as returned by GROUP BY query)
SAMPLE_FAC_AGG = [
    {"state": "CA", "facility_count": "120", "avg_rating": "3.5"},
    {"state": "TX", "facility_count": "95",  "avg_rating": "2.8"},
    {"state": "FL", "facility_count": "80",  "avg_rating": "3.1"},
]

# Sample flat facility rows (for facility_id → state mapping)
SAMPLE_FAC_FLAT = [
    {"facility_id": "100001", "state": "CA"},
    {"facility_id": "100002", "state": "TX"},
    {"facility_id": "100003", "state": "FL"},
    {"facility_id": "100004", "state": "TX"},
]

# Sample quality rows (worse than national)
SAMPLE_QUAL_WORSE = [
    {"facility_id": "100002", "compared_to_national": "Worse Than the National Rate"},
    {"facility_id": "100004", "compared_to_national": "Worse Than the National Rate"},
]


def _make_side_effect(agg_rows, flat_rows, qual_rows):
    """Return a side_effect that sequences three successive query calls."""
    calls = [agg_rows, flat_rows, qual_rows]
    call_count = [0]

    def side_effect(dataset_id, sql):
        idx = call_count[0]
        call_count[0] += 1
        return calls[idx] if idx < len(calls) else []

    return side_effect


@pytest.mark.asyncio
async def test_state_ranking_returns_expected_structure(mock_domo):
    """Tool returns required top-level keys."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FAC_AGG, SAMPLE_FAC_FLAT, SAMPLE_QUAL_WORSE
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {})

    assert "rankings" in result
    assert "total_states" in result
    assert "order" in result
    assert "clinical_context" in result


@pytest.mark.asyncio
async def test_state_ranking_worst_order_default(mock_domo):
    """Default order is 'worst' — lowest composite score first."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FAC_AGG, SAMPLE_FAC_FLAT, SAMPLE_QUAL_WORSE
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {})

    assert result["order"] == "worst"
    scores = [r["composite_score"] for r in result["rankings"]]
    assert scores == sorted(scores)


@pytest.mark.asyncio
async def test_state_ranking_best_order(mock_domo):
    """order='best' returns highest composite score first."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FAC_AGG, SAMPLE_FAC_FLAT, SAMPLE_QUAL_WORSE
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"order": "best"})

    assert result["order"] == "best"
    scores = [r["composite_score"] for r in result["rankings"]]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_state_ranking_limit_applied(mock_domo):
    """limit parameter caps the number of returned rankings."""
    # 3 states but limit=2
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FAC_AGG, SAMPLE_FAC_FLAT, SAMPLE_QUAL_WORSE
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"limit": 2})

    assert len(result["rankings"]) <= 2
    assert result["total_states"] == 3  # total_states still reflects all valid states


@pytest.mark.asyncio
async def test_state_ranking_ranking_fields(mock_domo):
    """Each ranking entry contains all expected fields."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FAC_AGG, SAMPLE_FAC_FLAT, SAMPLE_QUAL_WORSE
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {})

    for entry in result["rankings"]:
        assert "state" in entry
        assert "facility_count" in entry
        assert "avg_star_rating" in entry
        assert "worse_than_national_count" in entry
        assert "worse_than_national_pct" in entry
        assert "composite_score" in entry


@pytest.mark.asyncio
async def test_state_ranking_missing_fac_id_returns_error(mock_domo):
    """Returns error dict when HP_FACILITIES_DATASET_ID is not set."""
    with patch.dict("os.environ", {}, clear=True):
        result = await run(mock_domo, {})

    assert "error" in result
    assert "HP_FACILITIES_DATASET_ID" in result["error"]


@pytest.mark.asyncio
async def test_state_ranking_ignores_invalid_state_codes(mock_domo):
    """Rows with state codes that are not exactly 2 characters are skipped."""
    bad_rows = [
        {"state": "CA", "facility_count": "50", "avg_rating": "3.0"},
        {"state": "INVALID", "facility_count": "10", "avg_rating": "2.0"},
        {"state": "",  "facility_count": "5",  "avg_rating": "1.0"},
    ]
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        bad_rows, SAMPLE_FAC_FLAT, SAMPLE_QUAL_WORSE
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {})

    # Only "CA" is valid
    states = [r["state"] for r in result["rankings"]]
    assert "INVALID" not in states
    assert "" not in states
    assert "CA" in states


@pytest.mark.asyncio
async def test_state_ranking_composite_score_range(mock_domo):
    """All composite scores are in the 0-100 range."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FAC_AGG, SAMPLE_FAC_FLAT, SAMPLE_QUAL_WORSE
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"limit": 50})

    for entry in result["rankings"]:
        assert 0 <= entry["composite_score"] <= 100
