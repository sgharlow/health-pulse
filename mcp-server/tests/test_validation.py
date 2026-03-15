"""Tests for input validation."""
from healthpulse_mcp.validation import validate_state, validate_facility_id, validate_facility_ids


def test_validate_state_valid():
    assert validate_state("CA") == "CA"
    assert validate_state("ca") == "CA"
    assert validate_state(" ny ") == "NY"


def test_validate_state_invalid():
    assert validate_state("'; DROP TABLE--") is None
    assert validate_state("California") is None
    assert validate_state("") is None
    assert validate_state(None) is None


def test_validate_facility_id_valid():
    assert validate_facility_id("050454") == "050454"
    assert validate_facility_id("330214") == "330214"


def test_validate_facility_id_invalid():
    assert validate_facility_id("'; DROP--") is None
    assert validate_facility_id("") is None


def test_validate_facility_ids_filters():
    result = validate_facility_ids(["050454", "bad'; DROP", "330214"])
    assert result == ["050454", "330214"]
