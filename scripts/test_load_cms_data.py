"""Tests for CMS data cleaning logic (no Domo dependency)."""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))

from load_cms_data import (
    MORTALITY_MEASURES, TIMELY_MEASURES, HCAHPS_COMPOSITES,
    READM_30_PREFIX, _is_hcahps_composite,
)


def test_mortality_measures_are_defined():
    assert len(MORTALITY_MEASURES) == 7
    assert "MORT_30_AMI" in MORTALITY_MEASURES
    assert "PSI_90_SAFETY" in MORTALITY_MEASURES


def test_timely_measures_are_defined():
    assert len(TIMELY_MEASURES) >= 4
    assert "SEP_1" in TIMELY_MEASURES
    assert "OP_18b" in TIMELY_MEASURES


def test_readm_prefix():
    assert READM_30_PREFIX == "READM_30"
    assert "READM_30_HF".startswith(READM_30_PREFIX)


def test_hcahps_composites_filter():
    test_ids = ["H_COMP_1", "H_CLEAN_LINEAR", "H_STAR_RATING",
                "H_RECMND", "H_QUIET_HSP_A_P"]
    kept = [x for x in test_ids if _is_hcahps_composite(x)]
    assert "H_COMP_1" in kept
    assert "H_CLEAN_LINEAR" in kept
    assert "H_STAR_RATING" in kept
    assert "H_QUIET_HSP_A_P" not in kept
