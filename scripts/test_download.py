"""Smoke test for CMS dataset configuration."""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))

from download_cms_data import CMS_DATASETS


def test_all_datasets_have_required_fields():
    for name, info in CMS_DATASETS.items():
        assert "id" in info, f"{name} missing dataset id"
        assert "filename" in info, f"{name} missing filename"
        assert info["filename"].endswith(".csv"), f"{name} filename must end in .csv"


def test_dataset_count():
    assert len(CMS_DATASETS) == 9
