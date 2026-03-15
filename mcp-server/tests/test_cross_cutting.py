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


def _make_side_effect(fac_rows, qual_rows, readm_rows, svi_rows=None):
    """Sequence four query calls: facilities, quality, readmissions, [SVI]."""
    sequence = [fac_rows, qual_rows, readm_rows]
    if svi_rows is not None:
        sequence.append(svi_rows)
    call_count = [0]

    def side_effect(dataset_id, sql):
        idx = call_count[0]
        call_count[0] += 1
        return sequence[idx] if idx < len(sequence) else []

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
    # First call is facilities, third call is readmissions — both should have state filter
    assert "WHERE state = 'TX'" in calls[0][0][1]
    assert "WHERE state = 'TX'" in calls[2][0][1]


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

    mock_domo.query_as_dicts.side_effect = _make_side_effect(fac_rows, qual_rows, readm_rows)

    with patch.dict("os.environ", ENV_NO_COM):
        result = await run(mock_domo, {})

    assert len(result["multi_concern_facilities"]) <= 15
    assert result["total_multi_concern"] == 20
