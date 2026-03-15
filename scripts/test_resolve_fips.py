"""Tests for FIPS code resolution."""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))

from resolve_fips import normalize_county, resolve_fips


def test_normalize_removes_county_suffix():
    assert normalize_county("Los Angeles County") == "LOS ANGELES"


def test_normalize_removes_parish_suffix():
    assert normalize_county("Orleans Parish") == "ORLEANS"


def test_normalize_saint_abbreviation():
    assert normalize_county("St. Louis County") == "SAINT LOUIS"


def test_normalize_preserves_base_name():
    assert normalize_county("COOK") == "COOK"


def test_resolve_fips_with_known_lookup():
    lookup = {("CA", "LOS ANGELES"): "06037", ("IL", "COOK"): "17031"}
    assert resolve_fips("CA", "Los Angeles County", lookup) == "06037"
    assert resolve_fips("IL", "Cook", lookup) == "17031"


def test_resolve_fips_returns_none_for_unknown():
    lookup = {("CA", "LOS ANGELES"): "06037"}
    assert resolve_fips("XX", "Nowhere", lookup) is None
