"""Tests for the facility_benchmark tool."""

import pytest
from unittest.mock import patch

from healthpulse_mcp.tools.facility_benchmark import run


ENV = {
    "HP_FACILITIES_DATASET_ID": "facilities-dataset-123",
    "HP_QUALITY_DATASET_ID": "quality-dataset-123",
    "HP_READMISSIONS_DATASET_ID": "readm-dataset-123",
}


def _make_side_effect(fac_rows, quality_rows, readm_rows):
    """Return a side_effect function that returns rows in call order."""
    results = [fac_rows, quality_rows, readm_rows]
    call_count = [0]

    def side_effect(dataset_id, sql):
        idx = call_count[0]
        call_count[0] += 1
        return results[idx]

    return side_effect


@pytest.mark.asyncio
async def test_facility_benchmark_returns_expected_structure(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """Tool returns required top-level keys."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"facility_ids": ["100001", "100002"]})

    assert "facilities" in result
    assert "comparison_count" in result


@pytest.mark.asyncio
async def test_facility_benchmark_returns_requested_facilities(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """Returns data for the requested facility IDs."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"facility_ids": ["100001", "100002"]})

    assert result["comparison_count"] == 2
    facility_ids = [f["facility_id"] for f in result["facilities"]]
    assert "100001" in facility_ids
    assert "100002" in facility_ids


@pytest.mark.asyncio
async def test_facility_benchmark_preserves_order(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """Facilities are returned in the same order as facility_ids input."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"facility_ids": ["100002", "100001"]})

    ids = [f["facility_id"] for f in result["facilities"]]
    assert ids == ["100002", "100001"]


@pytest.mark.asyncio
async def test_facility_benchmark_nested_quality_measures(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """Each facility has quality_measures list."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"facility_ids": ["100001"]})

    facility = result["facilities"][0]
    assert "quality_measures" in facility
    assert isinstance(facility["quality_measures"], list)


@pytest.mark.asyncio
async def test_facility_benchmark_nested_readmission_measures(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """Each facility has readmission_measures list."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"facility_ids": ["100001"]})

    facility = result["facilities"][0]
    assert "readmission_measures" in facility
    assert isinstance(facility["readmission_measures"], list)


@pytest.mark.asyncio
async def test_facility_benchmark_facility_not_in_dataset(
    mock_domo, sample_quality_rows, sample_readmission_rows
):
    """Unknown facility ID is included with a note."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        [],  # no facility found
        sample_quality_rows,
        sample_readmission_rows,
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"facility_ids": ["UNKNOWN_FAC"]})

    assert result["comparison_count"] == 1
    fac = result["facilities"][0]
    assert fac["facility_id"] == "UNKNOWN_FAC"
    assert "note" in fac


@pytest.mark.asyncio
async def test_facility_benchmark_measure_filter_in_sql(
    mock_domo, sample_facilities_rows, sample_quality_rows, sample_readmission_rows
):
    """measures filter is included in quality and readmissions SQL."""
    mock_domo.query_as_dicts.side_effect = _make_side_effect(
        sample_facilities_rows, sample_quality_rows, sample_readmission_rows
    )

    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {
            "facility_ids": ["100001"],
            "measures": ["MORT_30_AMI"],
        })

    calls = mock_domo.query_as_dicts.call_args_list
    # calls[1] = quality SQL, calls[2] = readmissions SQL
    assert "MORT_30_AMI" in calls[1][0][1]
    assert "MORT_30_AMI" in calls[2][0][1]


@pytest.mark.asyncio
async def test_facility_benchmark_requires_facility_ids(mock_domo):
    """Returns error when facility_ids is empty."""
    with patch.dict("os.environ", ENV):
        result = await run(mock_domo, {"facility_ids": []})

    assert "error" in result


@pytest.mark.asyncio
async def test_facility_benchmark_missing_facilities_id(mock_domo):
    """Returns error when HP_FACILITIES_DATASET_ID is not set."""
    with patch.dict("os.environ", {
        "HP_QUALITY_DATASET_ID": "q123",
        "HP_READMISSIONS_DATASET_ID": "r123",
    }, clear=True):
        result = await run(mock_domo, {"facility_ids": ["100001"]})

    assert "error" in result
    assert "HP_FACILITIES_DATASET_ID" in result["error"]
