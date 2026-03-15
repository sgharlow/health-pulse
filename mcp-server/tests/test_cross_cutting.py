"""Tests for the cross_cutting_analysis tool."""

import pytest
from unittest.mock import patch

from healthpulse_mcp.tools.cross_cutting_analysis import run


ENV_FULL = {
    "HP_FACILITIES_DATASET_ID": "fac-123",
    "HP_QUALITY_DATASET_ID": "qual-123",
    "HP_READMISSIONS_DATASET_ID": "readm-123",
    "HP_COMMUNITY_DATASET_ID": "com-123",
}

ENV_ALL_SIX = {
    **ENV_FULL,
    "HP_EXPERIENCE_DATASET_ID": "exp-123",
    "HP_COST_DATASET_ID": "cost-123",
}

ENV_NO_COM = {
    "HP_FACILITIES_DATASET_ID": "fac-123",
    "HP_QUALITY_DATASET_ID": "qual-123",
    "HP_READMISSIONS_DATASET_ID": "readm-123",
}

SAMPLE_FACILITIES = [
    {
        "facility_id": "100001",
        "facility_name": "Troubled Medical Center",
        "state": "TX",
        "hospital_overall_rating": "1",
        "county_fips": "48201",
    },
    {
        "facility_id": "100002",
        "facility_name": "Average Community Hospital",
        "state": "TX",
        "hospital_overall_rating": "3",
        "county_fips": "48113",
    },
    {
        "facility_id": "100003",
        "facility_name": "High Performer",
        "state": "TX",
        "hospital_overall_rating": "5",
        "county_fips": "48029",
    },
]

SAMPLE_QUALITY_WORSE = [
    # facility 100001 has 3 worse-than-national measures
    {"facility_id": "100001", "measure_id": "MORT_30_AMI",  "compared_to_national": "Worse Than the National Rate"},
    {"facility_id": "100001", "measure_id": "MORT_30_HF",   "compared_to_national": "Worse Than the National Rate"},
    {"facility_id": "100001", "measure_id": "PSI_90_SAFETY", "compared_to_national": "Worse Than the National Rate"},
    # facility 100002 has only 1 worse measure — should NOT trigger quality concern
    {"facility_id": "100002", "measure_id": "MORT_30_AMI",  "compared_to_national": "Worse Than the National Rate"},
]

SAMPLE_READMISSIONS = [
    # facility 100001: excess ratio > 1.05 → readmission concern
    {"facility_id": "100001", "measure_name": "AMI 30-Day Readmission", "excess_readmission_ratio": "1.18"},
    # facility 100002: ratio <= 1.05 → no concern
    {"facility_id": "100002", "measure_name": "HF 30-Day Readmission",  "excess_readmission_ratio": "1.03"},
    # facility 100003: no excess readmissions
    {"facility_id": "100003", "measure_name": "PN 30-Day Readmission",  "excess_readmission_ratio": "0.98"},
]

SAMPLE_SVI = [
    # 100001 county is high-vulnerability
    {"county_fips": "48201", "svi_score": "0.88", "poverty_rate": "22.5", "uninsured_rate": "18.0", "minority_pct": "65.0"},
    # 100002 county is low-vulnerability
    {"county_fips": "48113", "svi_score": "0.40", "poverty_rate": "10.0", "uninsured_rate": "8.0",  "minority_pct": "30.0"},
    # 100003 county is moderate
    {"county_fips": "48029", "svi_score": "0.55", "poverty_rate": "12.0", "uninsured_rate": "9.0",  "minority_pct": "35.0"},
]

SAMPLE_EXPERIENCE = [
    # 100001: low patient experience (star rating 2.0 for overall measures)
    {"facility_id": "100001", "patient_survey_star_rating": "2", "hcahps_answer_percent": "30"},
    {"facility_id": "100001", "patient_survey_star_rating": "2", "hcahps_answer_percent": "25"},
    # 100002: decent experience
    {"facility_id": "100002", "patient_survey_star_rating": "4", "hcahps_answer_percent": "75"},
    # 100003: great experience
    {"facility_id": "100003", "patient_survey_star_rating": "5", "hcahps_answer_percent": "90"},
]

SAMPLE_COST = [
    # 100001: overspending (ratio 1.25 > 1.1)
    {"facility_id": "100001", "score": "1.25"},
    # 100002: slightly over but below threshold
    {"facility_id": "100002", "score": "1.05"},
    # 100003: efficient
    {"facility_id": "100003", "score": "0.92"},
]


def _make_side_effect(fac_rows, qual_rows, readm_rows, svi_rows=None,
                      exp_rows=None, cost_rows=None):
    """Build a dataset-ID-based side effect for query_as_dicts.

    Maps dataset IDs to their corresponding mock data so the order of
    queries does not matter.
    """
    data_by_id = {
        "fac-123": fac_rows,
        "qual-123": qual_rows,
        "readm-123": readm_rows,
    }
    if svi_rows is not None:
        data_by_id["com-123"] = svi_rows
    if exp_rows is not None:
        data_by_id["exp-123"] = exp_rows
    if cost_rows is not None:
        data_by_id["cost-123"] = cost_rows

    def side_effect(dataset_id, sql):
        return data_by_id.get(dataset_id, [])

    return side_effect


@pytest.mark.asyncio
async def test_cross_cutting_returns_expected_structure(mock_domo):
    """Tool returns required top-level keys."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FACILITIES, SAMPLE_QUALITY_WORSE, SAMPLE_READMISSIONS, SAMPLE_SVI
    )

    with patch.dict("os.environ", ENV_FULL):
        result = await run(mock_domo, {})

    assert "multi_concern_facilities" in result
    assert "total_multi_concern" in result
    assert "total_facilities_analyzed" in result
    assert "systemic_patterns" in result
    assert "filters" in result
    assert "clinical_context" in result


@pytest.mark.asyncio
async def test_cross_cutting_identifies_multi_concern_facility(mock_domo):
    """Facility 100001 has quality + readmission + equity + low rating concerns."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FACILITIES, SAMPLE_QUALITY_WORSE, SAMPLE_READMISSIONS, SAMPLE_SVI
    )

    with patch.dict("os.environ", ENV_FULL):
        result = await run(mock_domo, {})

    facility_ids = [f["facility_id"] for f in result["multi_concern_facilities"]]
    assert "100001" in facility_ids

    troubled = next(f for f in result["multi_concern_facilities"] if f["facility_id"] == "100001")
    # Should have at least 3 concerns: quality (3 measures), readmission, low star rating
    assert troubled["concern_count"] >= 3


@pytest.mark.asyncio
async def test_cross_cutting_excludes_single_concern_facilities(mock_domo):
    """Facility 100003 (only good metrics) is excluded from multi-concern list."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FACILITIES, SAMPLE_QUALITY_WORSE, SAMPLE_READMISSIONS, SAMPLE_SVI
    )

    with patch.dict("os.environ", ENV_FULL):
        result = await run(mock_domo, {})

    facility_ids = [f["facility_id"] for f in result["multi_concern_facilities"]]
    # 100003 has no quality flags, no excess readmissions, moderate SVI, 5 stars
    assert "100003" not in facility_ids


@pytest.mark.asyncio
async def test_cross_cutting_sorted_by_concern_count_desc(mock_domo):
    """Results are sorted with most-concern facilities first."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FACILITIES, SAMPLE_QUALITY_WORSE, SAMPLE_READMISSIONS, SAMPLE_SVI
    )

    with patch.dict("os.environ", ENV_FULL):
        result = await run(mock_domo, {})

    counts = [f["concern_count"] for f in result["multi_concern_facilities"]]
    assert counts == sorted(counts, reverse=True)


@pytest.mark.asyncio
async def test_cross_cutting_missing_required_datasets_returns_error(mock_domo):
    """Returns error when required dataset IDs are missing."""
    with patch.dict("os.environ", {}, clear=True):
        result = await run(mock_domo, {})

    assert "error" in result


@pytest.mark.asyncio
async def test_cross_cutting_state_filter_passed_to_queries(mock_domo):
    """State filter is included in facility and readmission queries."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FACILITIES, SAMPLE_QUALITY_WORSE, SAMPLE_READMISSIONS
    )

    with patch.dict("os.environ", ENV_NO_COM):
        result = await run(mock_domo, {"state": "TX"})

    assert result["filters"]["state"] == "TX"
    calls = mock_domo.query_as_dicts.call_args_list
    # Find the facilities call (fac-123) and readmissions call (readm-123) by dataset_id
    fac_calls = [c for c in calls if c[0][0] == "fac-123"]
    readm_calls = [c for c in calls if c[0][0] == "readm-123"]
    assert fac_calls, "Expected a facilities query"
    assert readm_calls, "Expected a readmissions query"
    assert "WHERE state = 'TX'" in fac_calls[0][0][1]
    assert "WHERE state = 'TX'" in readm_calls[0][0][1]


@pytest.mark.asyncio
async def test_cross_cutting_without_community_dataset(mock_domo):
    """Tool works without community SVI data (no equity dimension)."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FACILITIES, SAMPLE_QUALITY_WORSE, SAMPLE_READMISSIONS
    )

    with patch.dict("os.environ", ENV_NO_COM):
        result = await run(mock_domo, {})

    # Should still succeed and return structure (just no SVI equity dimension)
    assert "multi_concern_facilities" in result
    assert "error" not in result


@pytest.mark.asyncio
async def test_cross_cutting_capped_at_15_results(mock_domo):
    """multi_concern_facilities list is capped at 15 entries."""
    # Create 20 facilities each with >= 2 concerns (low rating + quality flags)
    fac_rows = [
        {
            "facility_id": str(i),
            "facility_name": f"Hospital {i}",
            "state": "CA",
            "hospital_overall_rating": "1",
            "county_fips": f"{i:05d}",
        }
        for i in range(1, 21)
    ]
    qual_rows = [
        {"facility_id": str(i), "measure_id": m, "compared_to_national": "Worse Than the National Rate"}
        for i in range(1, 21)
        for m in ["MORT_30_AMI", "MORT_30_HF"]  # 2 measures each → triggers quality concern
    ]
    readm_rows = [
        {"facility_id": str(i), "measure_name": "AMI Readmission", "excess_readmission_ratio": "1.20"}
        for i in range(1, 21)
    ]

    # Use dataset-ID-based dispatch with custom IDs
    data_by_id = {
        "fac-123": fac_rows,
        "qual-123": qual_rows,
        "readm-123": readm_rows,
    }
    mock_domo.query_as_dicts.side_effect = lambda ds_id, sql: data_by_id.get(ds_id, [])

    with patch.dict("os.environ", ENV_NO_COM):
        result = await run(mock_domo, {})

    assert len(result["multi_concern_facilities"]) <= 15
    assert result["total_multi_concern"] == 20


# --- New tests for patient experience and cost efficiency dimensions ---


@pytest.mark.asyncio
async def test_cross_cutting_includes_patient_experience_concern(mock_domo):
    """Facility 100001 gets a patient experience concern when HCAHPS avg < 3.0."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FACILITIES, SAMPLE_QUALITY_WORSE, SAMPLE_READMISSIONS, SAMPLE_SVI,
        exp_rows=SAMPLE_EXPERIENCE, cost_rows=SAMPLE_COST,
    )

    with patch.dict("os.environ", ENV_ALL_SIX):
        result = await run(mock_domo, {})

    troubled = next(
        f for f in result["multi_concern_facilities"] if f["facility_id"] == "100001"
    )
    experience_concerns = [c for c in troubled["concerns"] if "patient experience" in c.lower()]
    assert len(experience_concerns) == 1
    assert "avg HCAHPS score 2.0" in experience_concerns[0]


@pytest.mark.asyncio
async def test_cross_cutting_includes_cost_concern(mock_domo):
    """Facility 100001 gets a cost overspending concern when MSPB ratio > 1.1."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FACILITIES, SAMPLE_QUALITY_WORSE, SAMPLE_READMISSIONS, SAMPLE_SVI,
        exp_rows=SAMPLE_EXPERIENCE, cost_rows=SAMPLE_COST,
    )

    with patch.dict("os.environ", ENV_ALL_SIX):
        result = await run(mock_domo, {})

    troubled = next(
        f for f in result["multi_concern_facilities"] if f["facility_id"] == "100001"
    )
    cost_concerns = [c for c in troubled["concerns"] if "cost overspending" in c.lower()]
    assert len(cost_concerns) == 1
    assert "MSPB ratio 1.25" in cost_concerns[0]


@pytest.mark.asyncio
async def test_cross_cutting_six_dimensions_increase_concern_count(mock_domo):
    """With all 6 dimensions, facility 100001 has more concerns than with 4."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FACILITIES, SAMPLE_QUALITY_WORSE, SAMPLE_READMISSIONS, SAMPLE_SVI,
        exp_rows=SAMPLE_EXPERIENCE, cost_rows=SAMPLE_COST,
    )

    with patch.dict("os.environ", ENV_ALL_SIX):
        result = await run(mock_domo, {})

    troubled = next(
        f for f in result["multi_concern_facilities"] if f["facility_id"] == "100001"
    )
    # quality + readmissions + SVI + star rating + experience + cost = 6
    assert troubled["concern_count"] == 6


@pytest.mark.asyncio
async def test_cross_cutting_no_experience_concern_for_good_facility(mock_domo):
    """Facility 100003 (high HCAHPS scores) has no patient experience concern."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FACILITIES, SAMPLE_QUALITY_WORSE, SAMPLE_READMISSIONS, SAMPLE_SVI,
        exp_rows=SAMPLE_EXPERIENCE, cost_rows=SAMPLE_COST,
    )

    with patch.dict("os.environ", ENV_ALL_SIX):
        result = await run(mock_domo, {})

    facility_ids = [f["facility_id"] for f in result["multi_concern_facilities"]]
    # 100003 should still not appear — all its scores are good
    assert "100003" not in facility_ids


@pytest.mark.asyncio
async def test_cross_cutting_no_cost_concern_below_threshold(mock_domo):
    """Facility 100002 (MSPB ratio 1.05, below 1.1) has no cost concern."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FACILITIES, SAMPLE_QUALITY_WORSE, SAMPLE_READMISSIONS, SAMPLE_SVI,
        exp_rows=SAMPLE_EXPERIENCE, cost_rows=SAMPLE_COST,
    )

    with patch.dict("os.environ", ENV_ALL_SIX):
        result = await run(mock_domo, {})

    # 100002 has only 1 quality flag (not enough) and MSPB 1.05 (below threshold)
    # So it should not appear in multi-concern (at most 0 concerns that trigger)
    facility_ids = [f["facility_id"] for f in result["multi_concern_facilities"]]
    assert "100002" not in facility_ids


@pytest.mark.asyncio
async def test_cross_cutting_skips_experience_when_env_not_set(mock_domo):
    """When HP_EXPERIENCE_DATASET_ID is not set, experience dimension is skipped."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FACILITIES, SAMPLE_QUALITY_WORSE, SAMPLE_READMISSIONS, SAMPLE_SVI
    )

    with patch.dict("os.environ", ENV_FULL):
        result = await run(mock_domo, {})

    assert "error" not in result
    # Should still work with 4 dimensions
    troubled = next(
        f for f in result["multi_concern_facilities"] if f["facility_id"] == "100001"
    )
    experience_concerns = [c for c in troubled["concerns"] if "patient experience" in c.lower()]
    assert len(experience_concerns) == 0


@pytest.mark.asyncio
async def test_cross_cutting_skips_cost_when_env_not_set(mock_domo):
    """When HP_COST_DATASET_ID is not set, cost dimension is skipped."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        SAMPLE_FACILITIES, SAMPLE_QUALITY_WORSE, SAMPLE_READMISSIONS, SAMPLE_SVI
    )

    with patch.dict("os.environ", ENV_FULL):
        result = await run(mock_domo, {})

    assert "error" not in result
    troubled = next(
        f for f in result["multi_concern_facilities"] if f["facility_id"] == "100001"
    )
    cost_concerns = [c for c in troubled["concerns"] if "cost overspending" in c.lower()]
    assert len(cost_concerns) == 0
