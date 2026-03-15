"""Tests for the cost_efficiency tool."""

import pytest
from unittest.mock import patch

from healthpulse_mcp.tools.cost_efficiency import run


ENV = {
    "HP_COST_DATASET_ID": "cost-dataset-123",
    "HP_FACILITIES_DATASET_ID": "facilities-dataset-123",
}


@pytest.fixture
def sample_cost_rows():
    """Sample Medicare spending per beneficiary rows."""
    return [
        {
            "facility_id": "100001",
            "score": "0.95",
            "avg_spending_hospital": "3600",
            "avg_spending_national": "3800",
        },
        {
            "facility_id": "100002",
            "score": "1.15",
            "avg_spending_hospital": "4370",
            "avg_spending_national": "3800",
        },
        {
            "facility_id": "100003",
            "score": "1.35",
            "avg_spending_hospital": "5130",
            "avg_spending_national": "3800",
        },
        {
            "facility_id": "100004",
            "score": "0.98",
            "avg_spending_hospital": "3724",
            "avg_spending_national": "3800",
        },
        {
            "facility_id": "100005",
            "score": "1.22",
            "avg_spending_hospital": "4636",
            "avg_spending_national": "3800",
        },
    ]


@pytest.fixture
def sample_cost_facilities_rows():
    """Sample facility rows with star ratings for cost-quality analysis."""
    return [
        {
            "facility_id": "100001",
            "facility_name": "General Hospital A",
            "state": "CA",
            "hospital_overall_rating": "4",
        },
        {
            "facility_id": "100002",
            "facility_name": "City Medical Center",
            "state": "CA",
            "hospital_overall_rating": "3",
        },
        {
            "facility_id": "100003",
            "facility_name": "Rural Health Clinic",
            "state": "CA",
            "hospital_overall_rating": "2",
        },
        {
            "facility_id": "100004",
            "facility_name": "Memorial Hospital",
            "state": "CA",
            "hospital_overall_rating": "5",
        },
        {
            "facility_id": "100005",
            "facility_name": "Valley Hospital",
            "state": "CA",
            "hospital_overall_rating": "1",
        },
    ]


@pytest.mark.asyncio
async def test_cost_efficiency_returns_expected_structure(
    mock_domo, sample_cost_rows, sample_cost_facilities_rows
):
    """Tool returns all required top-level keys."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_cost_rows
        return sample_cost_facilities_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {})

    assert "total_facilities_analyzed" in result
    assert "summary" in result
    assert "overspenders" in result
    assert "cost_quality_correlation" in result
    assert "clinical_context" in result
    assert "filters" in result


@pytest.mark.asyncio
async def test_cost_efficiency_summary_structure(
    mock_domo, sample_cost_rows, sample_cost_facilities_rows
):
    """Summary contains all expected keys."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_cost_rows
        return sample_cost_facilities_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {})

    summary = result["summary"]
    assert "avg_spending_ratio" in summary
    assert "overspending_count" in summary
    assert "overspending_pct" in summary
    assert "avg_national_spending" in summary
    assert "highest_spending_facility" in summary
    assert "highest_spending_ratio" in summary


@pytest.mark.asyncio
async def test_cost_efficiency_spending_ratio_calculation(
    mock_domo, sample_cost_rows, sample_cost_facilities_rows
):
    """Spending ratio is correctly calculated as hospital / national."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_cost_rows
        return sample_cost_facilities_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"spending_threshold": 1.1})

    # Facility 100003: 5130 / 3800 = 1.35 (highest ratio)
    assert result["summary"]["highest_spending_ratio"] == pytest.approx(1.35, abs=0.01)
    assert result["summary"]["highest_spending_facility"] == "Rural Health Clinic"


@pytest.mark.asyncio
async def test_cost_efficiency_identifies_overspenders(
    mock_domo, sample_cost_rows, sample_cost_facilities_rows
):
    """Facilities with spending ratio > threshold are flagged as overspenders."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_cost_rows
        return sample_cost_facilities_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"spending_threshold": 1.1})

    overspender_ids = [o["facility_id"] for o in result["overspenders"]]
    # 100002: 4370/3800=1.15 > 1.1 (overspender)
    # 100003: 5130/3800=1.35 > 1.1 (overspender)
    # 100005: 4636/3800=1.22 > 1.1 (overspender)
    assert "100002" in overspender_ids
    assert "100003" in overspender_ids
    assert "100005" in overspender_ids
    # 100001: 3600/3800=0.95 (not overspender)
    # 100004: 3724/3800=0.98 (not overspender)
    assert "100001" not in overspender_ids
    assert "100004" not in overspender_ids
    assert result["summary"]["overspending_count"] == 3


@pytest.mark.asyncio
async def test_cost_efficiency_overspenders_sorted_descending(
    mock_domo, sample_cost_rows, sample_cost_facilities_rows
):
    """Overspenders are sorted by spending ratio descending."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_cost_rows
        return sample_cost_facilities_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"spending_threshold": 1.1})

    ratios = [o["spending_ratio"] for o in result["overspenders"]]
    assert ratios == sorted(ratios, reverse=True)


@pytest.mark.asyncio
async def test_cost_efficiency_cost_quality_correlation(
    mock_domo, sample_cost_rows, sample_cost_facilities_rows
):
    """Cost-quality correlation correctly classifies facilities."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_cost_rows
        return sample_cost_facilities_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"spending_threshold": 1.1})

    corr = result["cost_quality_correlation"]
    # high cost (ratio>1.1): 100002 (rating=3), 100003 (rating=2), 100005 (rating=1)
    # low cost: 100001 (rating=4), 100004 (rating=5)
    # high_cost_low_quality: 100003 (rating=2) + 100005 (rating=1) = 2
    # high_cost_high_quality: 0 (no high-cost facility has rating >= 4)
    # low_cost_low_quality: 0
    # low_cost_high_quality: 100001 (rating=4) + 100004 (rating=5) = 2
    assert corr["high_cost_low_quality"] == 2
    assert corr["high_cost_high_quality"] == 0
    assert corr["low_cost_low_quality"] == 0
    assert corr["low_cost_high_quality"] == 2
    assert "insight" in corr


@pytest.mark.asyncio
async def test_cost_efficiency_state_filter(
    mock_domo, sample_cost_rows, sample_cost_facilities_rows
):
    """State filter is applied and reflected in filters output."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_cost_rows
        return sample_cost_facilities_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"state": "CA", "spending_threshold": 1.1})

    assert result["filters"]["state"] == "CA"
    # Facilities query should include state condition
    calls = mock_domo.query_as_dicts.call_args_list
    fac_call_sql = calls[1][0][1]
    assert "state = 'CA'" in fac_call_sql


@pytest.mark.asyncio
async def test_cost_efficiency_missing_cost_dataset_id(mock_domo):
    """Returns error when HP_COST_DATASET_ID is not set."""
    with patch.dict("os.environ", {"HP_FACILITIES_DATASET_ID": "f123"}, clear=True):
        result = await run(mock_domo, {})

    assert "error" in result
    assert "HP_COST_DATASET_ID" in result["error"]


@pytest.mark.asyncio
async def test_cost_efficiency_missing_facilities_dataset_id(mock_domo):
    """Returns error when HP_FACILITIES_DATASET_ID is not set."""
    with patch.dict("os.environ", {"HP_COST_DATASET_ID": "c123"}, clear=True):
        result = await run(mock_domo, {})

    assert "error" in result
    assert "HP_FACILITIES_DATASET_ID" in result["error"]


@pytest.mark.asyncio
async def test_cost_efficiency_empty_results(mock_domo):
    """Returns zero counts when no data rows match."""
    mock_domo.query_as_dicts.side_effect = [[], []]

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {})

    assert result["total_facilities_analyzed"] == 0
    assert result["summary"]["overspending_count"] == 0
    assert result["summary"]["overspending_pct"] == 0.0
    assert result["overspenders"] == []


@pytest.mark.asyncio
async def test_cost_efficiency_limit_caps_overspenders(mock_domo):
    """Overspenders list is capped at the limit parameter."""
    cost_rows = [
        {
            "facility_id": str(i),
            "score": "1.3",
            "avg_spending_hospital": "4940",
            "avg_spending_national": "3800",
        }
        for i in range(1, 31)
    ]
    fac_rows = [
        {
            "facility_id": str(i),
            "facility_name": f"Hospital {i}",
            "state": "TX",
            "hospital_overall_rating": "3",
        }
        for i in range(1, 31)
    ]
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return cost_rows
        return fac_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"spending_threshold": 1.1, "limit": 5})

    assert len(result["overspenders"]) == 5
    assert result["summary"]["overspending_count"] == 30


@pytest.mark.asyncio
async def test_cost_efficiency_clinical_context_present(
    mock_domo, sample_cost_rows, sample_cost_facilities_rows
):
    """Clinical context includes MSPB explanation."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_cost_rows
        return sample_cost_facilities_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {})

    ctx = result["clinical_context"]
    assert "about_mspb" in ctx
    assert "why_it_matters" in ctx
    assert "MSPB" in ctx["about_mspb"]


@pytest.mark.asyncio
async def test_cost_efficiency_cache_hit(
    mock_domo, sample_cost_rows, sample_cost_facilities_rows
):
    """Second call with same args returns cached result without querying Domo."""
    call_count = 0

    def side_effect(dataset_id, sql):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_cost_rows
        return sample_cost_facilities_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    with patch.dict("os.environ", ENV):
        result1 = await run(mock_domo, {"spending_threshold": 1.1})
        # Reset side_effect to verify no additional calls
        mock_domo.query_as_dicts.reset_mock()
        result2 = await run(mock_domo, {"spending_threshold": 1.1})

    assert result1 == result2
    mock_domo.query_as_dicts.assert_not_called()
