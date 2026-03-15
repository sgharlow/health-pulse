"""Tests for the executive_briefing tool."""

import pytest
from unittest.mock import patch

from healthpulse_mcp.tools.executive_briefing import run


ENV = {
    "HP_FACILITIES_DATASET_ID": "facilities-dataset-123",
    "HP_QUALITY_DATASET_ID": "quality-dataset-123",
    "HP_READMISSIONS_DATASET_ID": "readm-dataset-123",
}

ENV_WITH_COMMUNITY = {
    **ENV,
    "HP_COMMUNITY_DATASET_ID": "community-dataset-123",
}


def _make_side_effect(fac_rows, quality_rows, readm_rows, svi_rows=None):
    """Return a side_effect that delivers rows in call order."""
    all_results = [fac_rows, quality_rows, readm_rows]
    if svi_rows is not None:
        all_results.append(svi_rows)
    call_count = [0]

    def side_effect(dataset_id, sql):
        idx = call_count[0]
        call_count[0] += 1
        if idx < len(all_results):
            return all_results[idx]
        return []

    return side_effect


@pytest.mark.asyncio
async def test_executive_briefing_returns_expected_structure(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """Tool returns required top-level keys."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"scope": "network", "include_equity": False})

    assert "summary_stats" in result
    assert "anomalies" in result
    assert "care_gaps" in result
    assert "top_performers" in result
    assert "bottom_performers" in result
    assert "suggested_prompt" in result
    assert "filters" in result
    assert "clinical_context" in result


@pytest.mark.asyncio
async def test_executive_briefing_summary_stats_keys(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """Summary stats contains required keys."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"scope": "network", "include_equity": False})

    stats = result["summary_stats"]
    assert "total_facilities" in stats
    assert "anomaly_count" in stats
    assert "care_gap_count" in stats
    assert "avg_star_rating" in stats


@pytest.mark.asyncio
async def test_executive_briefing_total_facilities_count(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """total_facilities matches the number of facility rows returned."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"scope": "network", "include_equity": False})

    assert result["summary_stats"]["total_facilities"] == len(sample_facilities_rows)


@pytest.mark.asyncio
async def test_executive_briefing_avg_star_rating(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """avg_star_rating is computed correctly from facility ratings."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"scope": "network", "include_equity": False})

    # Ratings: 4, 3, 2 → avg = 3.0
    assert result["summary_stats"]["avg_star_rating"] == 3.0


@pytest.mark.asyncio
async def test_executive_briefing_care_gaps_filter_threshold(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """Only readmission rows with ratio > 1.05 are care gaps."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"scope": "network", "include_equity": False})

    # sample_readmission_rows: 1.02 (no), 1.15 (yes), 1.08 (yes) → 2 gaps
    assert result["summary_stats"]["care_gap_count"] == 2


@pytest.mark.asyncio
async def test_executive_briefing_suggested_prompt_is_string(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """suggested_prompt is a non-empty string."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"scope": "network", "include_equity": False})

    assert isinstance(result["suggested_prompt"], str)
    assert len(result["suggested_prompt"]) > 20


@pytest.mark.asyncio
async def test_executive_briefing_does_not_call_llm(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """Tool returns data; narrative text is only in suggested_prompt, not generated."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"scope": "network", "include_equity": False})

    # There should be no "narrative" key — just data + suggested_prompt
    assert "narrative" not in result


@pytest.mark.asyncio
async def test_executive_briefing_state_scope_applies_filter(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """State scope passes state condition to facilities and readmissions queries.

    Quality dataset does NOT have a 'state' column, so the state filter for quality
    is applied in Python (not in SQL). Facilities and readmissions queries must have
    the state = 'CA' condition; the quality query must not.
    """
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"scope": "state", "state": "CA", "include_equity": False})

    assert result["filters"]["state"] == "CA"
    calls = mock_domo.query_as_dicts.call_args_list
    # call 0 = facilities (has state), call 1 = quality (no state in SQL), call 2 = readmissions (has state)
    assert "state = 'CA'" in calls[0][0][1], "Facilities query must include state filter"
    assert "state = 'CA'" in calls[2][0][1], "Readmissions query must include state filter"
    assert "state = 'CA'" not in calls[1][0][1], "Quality query must NOT include state in SQL (filtered in Python)"


@pytest.mark.asyncio
async def test_executive_briefing_include_equity_returns_equity_summary(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows, sample_svi_rows
):
    """include_equity=True returns equity_summary key."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows, sample_svi_rows
    )

    with patch.dict("os.environ", ENV_WITH_COMMUNITY):
        result = await run(mock_domo, {"scope": "network", "include_equity": True})

    assert "equity_summary" in result
    assert "high_vulnerability_counties" in result["equity_summary"]


@pytest.mark.asyncio
async def test_executive_briefing_anomalies_capped_at_10(
    mock_domo, sample_quality_rows, sample_readmission_rows
):
    """anomalies is capped at 10."""
    # Build many quality rows to trigger many anomalies
    quality_rows = [
        {"facility_id": str(i), "facility_name": f"H{i}", "state": "NY",
         "measure_id": "MORT_30_AMI", "score": str(float(i * 3)),
         "compared_to_national": "No Different Than the National Rate"}
        for i in range(1, 25)
    ]
    fac_rows = [
        {"facility_id": str(i), "facility_name": f"H{i}", "state": "NY", "hospital_overall_rating": "3"}
        for i in range(1, 25)
    ]
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        fac_rows, quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"scope": "network", "include_equity": False})

    assert len(result["anomalies"]) <= 10


@pytest.mark.asyncio
async def test_executive_briefing_top_performers_structure(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """top_performers contains facility entries sorted by star_rating descending."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"scope": "network", "include_equity": False})

    top = result["top_performers"]
    assert len(top) > 0
    assert len(top) <= 5
    # Each entry has expected keys
    for entry in top:
        assert "facility" in entry
        assert "star_rating" in entry
        assert "state" in entry
        assert "type" in entry
    # Sorted descending
    ratings = [e["star_rating"] for e in top]
    assert ratings == sorted(ratings, reverse=True)


@pytest.mark.asyncio
async def test_executive_briefing_bottom_performers_structure(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """bottom_performers contains facility entries sorted by star_rating ascending."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"scope": "network", "include_equity": False})

    bottom = result["bottom_performers"]
    assert len(bottom) > 0
    assert len(bottom) <= 5
    # Sorted ascending
    ratings = [e["star_rating"] for e in bottom]
    assert ratings == sorted(ratings)


@pytest.mark.asyncio
async def test_executive_briefing_top_performer_is_highest_rated(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """First top_performer should be the highest-rated facility."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"scope": "network", "include_equity": False})

    # sample_facilities_rows ratings: 4, 3, 2 → top should be 4
    assert result["top_performers"][0]["star_rating"] == 4
    assert result["bottom_performers"][0]["star_rating"] == 2


@pytest.mark.asyncio
async def test_executive_briefing_equity_flags_returned(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows, sample_svi_rows
):
    """include_equity=True returns equity_flags array with per-facility entries."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows, sample_svi_rows
    )

    with patch.dict("os.environ", ENV_WITH_COMMUNITY):
        result = await run(mock_domo, {"scope": "network", "include_equity": True})

    assert "equity_flags" in result
    flags = result["equity_flags"]
    assert isinstance(flags, list)
    # sample_svi_rows has 2 high-SVI counties (06037=0.82, 06019=0.91)
    # so 2 facilities should be flagged (100001 in 06037, 100003 in 06019)
    assert len(flags) == 2
    for flag in flags:
        assert "facility" in flag
        assert "svi_score" in flag
        assert "outcome_gap" in flag
        assert flag["svi_score"] >= 0.75


@pytest.mark.asyncio
async def test_executive_briefing_equity_flags_sorted_by_svi(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows, sample_svi_rows
):
    """equity_flags are sorted by svi_score descending."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows, sample_svi_rows
    )

    with patch.dict("os.environ", ENV_WITH_COMMUNITY):
        result = await run(mock_domo, {"scope": "network", "include_equity": True})

    flags = result["equity_flags"]
    svi_scores = [f["svi_score"] for f in flags]
    assert svi_scores == sorted(svi_scores, reverse=True)


@pytest.mark.asyncio
async def test_executive_briefing_equity_flags_outcome_gap_content(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows, sample_svi_rows
):
    """equity_flags outcome_gap reflects actual care gap data for that facility."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows, sample_svi_rows
    )

    with patch.dict("os.environ", ENV_WITH_COMMUNITY):
        result = await run(mock_domo, {"scope": "network", "include_equity": True})

    flags = result["equity_flags"]
    # Fresno facility (100003, SVI 0.91) has a care gap (ratio 1.08)
    fresno_flag = [f for f in flags if f["svi_score"] == 0.91][0]
    assert "Excess readmission ratio" in fresno_flag["outcome_gap"]


@pytest.mark.asyncio
async def test_executive_briefing_no_equity_flags_when_equity_disabled(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """equity_flags not present when include_equity=False."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"scope": "network", "include_equity": False})

    assert "equity_flags" not in result


@pytest.mark.asyncio
async def test_executive_briefing_missing_facilities_id(mock_domo):
    """Returns error when HP_FACILITIES_DATASET_ID is not set."""
    with patch.dict("os.environ", {
        "HP_QUALITY_DATASET_ID": "q123",
        "HP_READMISSIONS_DATASET_ID": "r123",
    }, clear=True):
        result = await run(mock_domo, {"scope": "network"})

    assert "error" in result
