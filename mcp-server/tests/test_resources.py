"""Tests for MCP resource endpoints (facilities, facility/{id}, measures/{group})."""

import json
import os
import pytest
from unittest.mock import patch, MagicMock

from healthpulse_mcp.server import (
    list_facilities,
    list_states,
    list_measures,
    about_server,
    get_facility,
    get_measures_by_group,
    _MEASURE_GROUPS,
)


ENV = {"HP_FACILITIES_DATASET_ID": "facilities-dataset-123"}


# ---------------------------------------------------------------------------
# healthpulse://facilities
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_facilities_returns_facility_list(mock_domo, sample_facilities_rows):
    """Facilities resource returns a list of facility dicts."""
    mock_domo.query_as_dicts.return_value = sample_facilities_rows

    with patch.dict("os.environ", ENV), \
         patch("healthpulse_mcp.server._get_domo_client", return_value=mock_domo):
        result = json.loads(await list_facilities())

    assert "facilities" in result
    assert "total_returned" in result
    assert result["total_returned"] == 3
    assert result["facilities"][0]["facility_id"] == "100001"


@pytest.mark.asyncio
async def test_list_facilities_sql_has_limit(mock_domo, sample_facilities_rows):
    """Facilities resource query includes LIMIT 200 to avoid returning 5400 rows."""
    mock_domo.query_as_dicts.return_value = sample_facilities_rows

    with patch.dict("os.environ", ENV), \
         patch("healthpulse_mcp.server._get_domo_client", return_value=mock_domo):
        await list_facilities()

    called_sql = mock_domo.query_as_dicts.call_args[0][1]
    assert "LIMIT 200" in called_sql


@pytest.mark.asyncio
async def test_list_facilities_missing_env_var(mock_domo):
    """Returns error when HP_FACILITIES_DATASET_ID is not configured."""
    with patch.dict("os.environ", {}, clear=True):
        result = json.loads(await list_facilities())

    assert "error" in result
    assert "HP_FACILITIES_DATASET_ID" in result["error"]


@pytest.mark.asyncio
async def test_list_facilities_handles_domo_error(mock_domo):
    """Returns error when Domo query raises an exception."""
    mock_domo.query_as_dicts.side_effect = RuntimeError("Domo connection failed")

    with patch.dict("os.environ", ENV), \
         patch("healthpulse_mcp.server._get_domo_client", return_value=mock_domo):
        result = json.loads(await list_facilities())

    assert "error" in result
    assert "Domo connection failed" in result["error"]


# ---------------------------------------------------------------------------
# healthpulse://facilities/{facility_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_facility_returns_single_facility(mock_domo, sample_facilities_rows):
    """Facility detail resource returns a single facility dict."""
    mock_domo.query_as_dicts.return_value = [sample_facilities_rows[0]]

    with patch.dict("os.environ", ENV), \
         patch("healthpulse_mcp.server._get_domo_client", return_value=mock_domo):
        result = json.loads(await get_facility("100001"))

    assert "facility" in result
    assert result["facility"]["facility_id"] == "100001"
    assert result["facility"]["facility_name"] == "General Hospital A"


@pytest.mark.asyncio
async def test_get_facility_filters_by_id(mock_domo, sample_facilities_rows):
    """Facility detail query includes WHERE facility_id = '<id>'."""
    mock_domo.query_as_dicts.return_value = [sample_facilities_rows[1]]

    with patch.dict("os.environ", ENV), \
         patch("healthpulse_mcp.server._get_domo_client", return_value=mock_domo):
        await get_facility("100002")

    called_sql = mock_domo.query_as_dicts.call_args[0][1]
    assert "WHERE facility_id = '100002'" in called_sql


@pytest.mark.asyncio
async def test_get_facility_not_found(mock_domo):
    """Returns error when facility ID is not in the dataset."""
    mock_domo.query_as_dicts.return_value = []

    with patch.dict("os.environ", ENV), \
         patch("healthpulse_mcp.server._get_domo_client", return_value=mock_domo):
        result = json.loads(await get_facility("999999"))

    assert "error" in result
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_get_facility_invalid_id():
    """Returns error for malformed facility IDs (SQL injection prevention)."""
    with patch.dict("os.environ", ENV):
        result = json.loads(await get_facility("'; DROP TABLE--"))
    assert "error" in result
    assert "Invalid facility ID" in result["error"]


@pytest.mark.asyncio
async def test_get_facility_missing_env_var():
    """Returns error when HP_FACILITIES_DATASET_ID is not configured."""
    with patch.dict("os.environ", {}, clear=True):
        result = json.loads(await get_facility("050454"))

    assert "error" in result
    assert "HP_FACILITIES_DATASET_ID" in result["error"]


@pytest.mark.asyncio
async def test_get_facility_handles_domo_error(mock_domo):
    """Returns error when Domo query raises an exception."""
    mock_domo.query_as_dicts.side_effect = RuntimeError("Timeout")

    with patch.dict("os.environ", ENV), \
         patch("healthpulse_mcp.server._get_domo_client", return_value=mock_domo):
        result = json.loads(await get_facility("100001"))

    assert "error" in result
    assert "Timeout" in result["error"]


# ---------------------------------------------------------------------------
# healthpulse://measures/{group}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_measures_mortality():
    """Mortality group returns mortality measures."""
    result = json.loads(await get_measures_by_group("mortality"))

    assert result["group"] == "mortality"
    assert "MORT_30_AMI" in result["measures"]
    assert "MORT_30_HF" in result["measures"]
    assert result["total_measures"] == len(_MEASURE_GROUPS["mortality"])


@pytest.mark.asyncio
async def test_get_measures_readmission():
    """Readmission group returns readmission measures."""
    result = json.loads(await get_measures_by_group("readmission"))

    assert result["group"] == "readmission"
    assert "READM_30_AMI" in result["measures"]
    assert result["total_measures"] == len(_MEASURE_GROUPS["readmission"])


@pytest.mark.asyncio
async def test_get_measures_safety():
    """Safety group returns safety measures."""
    result = json.loads(await get_measures_by_group("safety"))

    assert result["group"] == "safety"
    assert "PSI_90_SAFETY" in result["measures"]
    assert result["total_measures"] == len(_MEASURE_GROUPS["safety"])


@pytest.mark.asyncio
async def test_get_measures_timeliness():
    """Timeliness group returns timeliness measures."""
    result = json.loads(await get_measures_by_group("timeliness"))

    assert result["group"] == "timeliness"
    assert "OP_18b" in result["measures"]
    assert "SEP_1" in result["measures"]
    assert result["total_measures"] == len(_MEASURE_GROUPS["timeliness"])


@pytest.mark.asyncio
async def test_get_measures_invalid_group():
    """Unknown group returns error with valid group names."""
    result = json.loads(await get_measures_by_group("invalid_group"))

    assert "error" in result
    assert "Unknown measure group" in result["error"]
    assert "valid_groups" in result
    assert "mortality" in result["valid_groups"]
    assert "readmission" in result["valid_groups"]
    assert "safety" in result["valid_groups"]
    assert "timeliness" in result["valid_groups"]


@pytest.mark.asyncio
async def test_get_measures_all_groups_have_entries():
    """Every defined group has at least one measure."""
    for group_name in _MEASURE_GROUPS:
        result = json.loads(await get_measures_by_group(group_name))
        assert result["total_measures"] > 0, f"Group {group_name!r} has no measures"


# ---------------------------------------------------------------------------
# Existing resources still work (regression)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_states_returns_states(mock_domo):
    """States resource returns expected structure."""
    mock_domo.query_as_dicts.return_value = [
        {"state": "CA", "facility_count": 400},
        {"state": "TX", "facility_count": 350},
    ]

    with patch.dict("os.environ", ENV), \
         patch("healthpulse_mcp.server._get_domo_client", return_value=mock_domo):
        result = json.loads(await list_states())

    assert "states" in result
    assert "total_states" in result
    assert result["total_states"] == 2


@pytest.mark.asyncio
async def test_list_measures_returns_flat_dict():
    """Measures resource returns a flat dict of all measures."""
    result = json.loads(await list_measures())

    assert "measures" in result
    assert "total_measures" in result
    assert "MORT_30_AMI" in result["measures"]


@pytest.mark.asyncio
async def test_about_server_returns_metadata():
    """About resource returns server metadata."""
    result = json.loads(await about_server())

    assert result["name"] == "HealthPulse AI"
    assert "tools" in result
    assert "data_sources" in result
