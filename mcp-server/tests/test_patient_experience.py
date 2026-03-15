"""Tests for the patient_experience tool."""

import pytest
from unittest.mock import patch

from healthpulse_mcp.tools.patient_experience import run


ENV = {
    "HP_EXPERIENCE_DATASET_ID": "experience-dataset-123",
    "HP_FACILITIES_DATASET_ID": "facilities-dataset-123",
}


@pytest.mark.asyncio
async def test_returns_expected_structure(mock_domo, sample_experience_rows):
    """Tool returns all required top-level keys."""
    mock_domo.query_as_dicts.return_value = sample_experience_rows

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure": "all"})

    assert "total_facilities_analyzed" in result
    assert "measure_category" in result
    assert "summary" in result
    assert "worst_facilities" in result
    assert "category_averages" in result
    assert "clinical_context" in result
    assert "filters" in result


@pytest.mark.asyncio
async def test_summary_has_required_fields(mock_domo, sample_experience_rows):
    """Summary dict contains avg_star_rating, lowest_category, and lowest_category_avg."""
    mock_domo.query_as_dicts.return_value = sample_experience_rows

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure": "all"})

    summary = result["summary"]
    assert "avg_star_rating" in summary
    assert "lowest_category" in summary
    assert "lowest_category_avg" in summary
    assert isinstance(summary["avg_star_rating"], float)


@pytest.mark.asyncio
async def test_category_averages_computed(mock_domo, sample_experience_rows):
    """Category averages are computed for all represented categories."""
    mock_domo.query_as_dicts.return_value = sample_experience_rows

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure": "all"})

    avgs = result["category_averages"]
    # Sample data has communication, responsiveness, environment, and overall measures
    assert "communication" in avgs
    assert "responsiveness" in avgs
    assert "environment" in avgs
    assert "overall" in avgs
    # All averages should be positive numbers (mix of star ratings 1-5 and percentages 0-100)
    for cat, avg in avgs.items():
        assert avg > 0, f"{cat} avg {avg} should be positive"


@pytest.mark.asyncio
async def test_worst_facilities_sorted_ascending(mock_domo, sample_experience_rows):
    """Worst facilities list is sorted by avg_experience_rating ascending (worst first)."""
    mock_domo.query_as_dicts.return_value = sample_experience_rows

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure": "all"})

    worst = result["worst_facilities"]
    assert len(worst) > 0
    ratings = [f["avg_experience_rating"] for f in worst]
    assert ratings == sorted(ratings), "Worst facilities should be sorted by rating ascending"
    # Facility 100002 has the worst scores — should be first
    assert worst[0]["facility_id"] == "100002"


@pytest.mark.asyncio
async def test_measure_category_filter_communication(mock_domo, sample_experience_rows):
    """measure='communication' only includes communication measures."""
    mock_domo.query_as_dicts.return_value = sample_experience_rows

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure": "communication"})

    assert result["measure_category"] == "communication"
    avgs = result["category_averages"]
    # Only communication category should be present
    assert "communication" in avgs
    assert "responsiveness" not in avgs
    assert "environment" not in avgs
    assert "overall" not in avgs


@pytest.mark.asyncio
async def test_measure_category_filter_responsiveness(mock_domo, sample_experience_rows):
    """measure='responsiveness' only includes responsiveness measures."""
    mock_domo.query_as_dicts.return_value = sample_experience_rows

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure": "responsiveness"})

    assert result["measure_category"] == "responsiveness"
    avgs = result["category_averages"]
    assert "responsiveness" in avgs
    assert "communication" not in avgs


@pytest.mark.asyncio
async def test_state_filter_queries_facilities_first(mock_domo, sample_experience_rows, sample_facilities_rows):
    """State filter queries facilities dataset first, then filters experience data in Python."""
    call_count = [0]

    def side_effect(dataset_id, sql):
        call_count[0] += 1
        if call_count[0] == 1:
            # First call: facilities query for state filter
            return sample_facilities_rows
        # Second call: experience query (all rows, filtered in Python)
        return sample_experience_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"state": "CA", "measure": "all"})

    assert result["filters"]["state"] == "CA"
    calls = mock_domo.query_as_dicts.call_args_list
    # First call (facilities) must include state = 'CA'
    assert "state = 'CA'" in calls[0][0][1]
    # Second call (experience) must NOT have state in SQL (uses facility_id filter in Python)
    assert "state" not in calls[1][0][1].lower()


@pytest.mark.asyncio
async def test_state_filter_enriches_worst_facilities(mock_domo, sample_experience_rows):
    """When state filter is used, worst facilities include facility_name and state."""
    fac_rows = [
        {"facility_id": "100001", "facility_name": "General Hospital A", "state": "CA"},
        {"facility_id": "100002", "facility_name": "City Medical Center", "state": "CA"},
        {"facility_id": "100003", "facility_name": "Rural Health Clinic", "state": "CA"},
    ]
    call_count = [0]

    def side_effect(dataset_id, sql):
        call_count[0] += 1
        if call_count[0] == 1:
            return fac_rows
        return sample_experience_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"state": "CA", "measure": "all"})

    worst = result["worst_facilities"]
    assert len(worst) > 0
    # All facilities with state lookup should have facility_name
    for fac in worst:
        assert "facility_name" in fac
        assert "state" in fac


@pytest.mark.asyncio
async def test_min_star_rating_filter(mock_domo, sample_experience_rows):
    """min_star_rating filters to rows with score below the threshold."""
    mock_domo.query_as_dicts.return_value = sample_experience_rows

    with patch.dict("os.environ", ENV):
        # Use threshold of 3.0 — only rows where the resolved score
        # (patient_survey_star_rating or hcahps_answer_percent fallback) < 3
        # are kept. Facility 100002 rows are all 1-2 so all pass.
        # Facility 100001 has mostly high-percent rows (55-78), only its
        # overall star ratings of 4 would not pass, but the percent rows
        # (>3) are also excluded. Effectively only 100002 qualifies.
        result = await run(mock_domo, {"measure": "all", "min_star_rating": 3.0})

    assert result["filters"]["min_star_rating"] == 3.0
    worst = result["worst_facilities"]
    # Only facility 100002 has all scores below 3
    assert len(worst) >= 1
    assert worst[0]["facility_id"] == "100002"


@pytest.mark.asyncio
async def test_limit_parameter(mock_domo, sample_experience_rows):
    """Limit parameter caps the number of worst facilities returned."""
    mock_domo.query_as_dicts.return_value = sample_experience_rows

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure": "all", "limit": 1})

    assert len(result["worst_facilities"]) <= 1


@pytest.mark.asyncio
async def test_empty_data(mock_domo):
    """Handles empty dataset gracefully."""
    mock_domo.query_as_dicts.return_value = []

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure": "all"})

    assert result["total_facilities_analyzed"] == 0
    assert result["worst_facilities"] == []
    assert result["category_averages"] == {}
    assert result["summary"]["avg_star_rating"] == 0.0


@pytest.mark.asyncio
async def test_missing_dataset_id(mock_domo):
    """Returns error dict when dataset ID env var is not set."""
    with patch.dict("os.environ", {}, clear=True):
        result = await run(mock_domo, {"measure": "all"})

    assert "error" in result
    assert "HP_EXPERIENCE_DATASET_ID" in result["error"]


@pytest.mark.asyncio
async def test_invalid_measure_category(mock_domo):
    """Returns error for invalid measure category."""
    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure": "invalid_category"})

    assert "error" in result
    assert "invalid_category" in result["error"]


@pytest.mark.asyncio
async def test_clinical_context_present(mock_domo, sample_experience_rows):
    """Clinical context includes HCAHPS description and VBP relevance."""
    mock_domo.query_as_dicts.return_value = sample_experience_rows

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure": "all"})

    ctx = result["clinical_context"]
    assert "about_hcahps" in ctx
    assert "HCAHPS" in ctx["about_hcahps"]
    assert "why_it_matters" in ctx
    assert "Value-Based Purchasing" in ctx["why_it_matters"]
    assert "measure_categories" in ctx


@pytest.mark.asyncio
async def test_cache_returns_same_result(mock_domo, sample_experience_rows):
    """Second call with same args returns cached result without querying Domo again."""
    mock_domo.query_as_dicts.return_value = sample_experience_rows

    with patch.dict("os.environ", ENV):
        result1 = await run(mock_domo, {"measure": "all"})
        result2 = await run(mock_domo, {"measure": "all"})

    assert result1 == result2
    # Domo should only be called once; second call uses cache
    assert mock_domo.query_as_dicts.call_count == 1


@pytest.mark.asyncio
async def test_query_failure_returns_error(mock_domo):
    """Returns error dict when Domo query raises an exception."""
    mock_domo.query_as_dicts.side_effect = Exception("Connection timeout")

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"measure": "all"})

    assert "error" in result
    assert "Query failed" in result["error"]


@pytest.mark.asyncio
async def test_facilities_missing_for_state_filter(mock_domo):
    """Returns error when state filter is used but HP_FACILITIES_DATASET_ID is missing."""
    env_no_fac = {"HP_EXPERIENCE_DATASET_ID": "experience-dataset-123"}

    with patch.dict("os.environ", env_no_fac, clear=True):
        result = await run(mock_domo, {"state": "CA", "measure": "all"})

    assert "error" in result
    assert "HP_FACILITIES_DATASET_ID" in result["error"]
