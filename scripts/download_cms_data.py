"""Download CMS Hospital Compare CSV files from data.cms.gov."""

import os
import sys
from pathlib import Path

import requests

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

CMS_DATASETS = {
    "hospital_general_info": {
        "id": "xubh-q36u",
        "filename": "Hospital_General_Information.csv",
    },
    "complications_deaths": {
        "id": "ynj2-r877",
        "filename": "Complications_and_Deaths-Hospital.csv",
    },
    "readmissions_hrrp": {
        "id": "9n3s-kdb3",
        "filename": "FY_2026_Hospital_Readmissions_Reduction_Program_Hospital.csv",
    },
    "hac_reduction": {
        "id": "yq43-i98g",
        "filename": "FY_2026_HAC_Reduction_Program_Hospital.csv",
    },
    "hcahps": {
        "id": "dgck-syfz",
        "filename": "HCAHPS-Hospital.csv",
    },
    "timely_effective_care": {
        "id": "yv7e-xc69",
        "filename": "Timely_and_Effective_Care-Hospital.csv",
    },
    "hai": {
        "id": "77hc-ibv8",
        "filename": "Healthcare_Associated_Infections-Hospital.csv",
    },
    "unplanned_visits": {
        "id": "632h-zaca",
        "filename": "Unplanned_Hospital_Visits-Hospital.csv",
    },
    "mspb_hospital": {
        "id": "rrqw-56er",
        "filename": "Medicare_Hospital_Spending_Per_Patient-Hospital.csv",
    },
}

API_BASE = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items"


def get_download_url(dataset_id: str) -> str:
    """Fetch the CSV download URL from CMS metadata API."""
    url = f"{API_BASE}/{dataset_id}?show-reference-ids"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    meta = resp.json()
    distributions = meta.get("distribution", [])
    for dist in distributions:
        data = dist.get("data", {})
        dl_url = data.get("downloadURL", "")
        if dl_url.endswith(".csv"):
            return dl_url
    raise ValueError(f"No CSV download URL found for dataset {dataset_id}")


def download_file(url: str, dest: Path) -> None:
    """Download a file with streaming."""
    print(f"  Downloading {dest.name}...")
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    size_mb = dest.stat().st_size / (1024 * 1024)
    print(f"  Done: {size_mb:.1f} MB")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading CMS datasets to {RAW_DIR}")

    for name, info in CMS_DATASETS.items():
        dest = RAW_DIR / info["filename"]
        if dest.exists():
            print(f"  Skipping {name} (already exists)")
            continue
        try:
            url = get_download_url(info["id"])
            download_file(url, dest)
        except Exception as e:
            print(f"  ERROR downloading {name}: {e}", file=sys.stderr)

    print(f"\nDone. {len(list(RAW_DIR.glob('*.csv')))} CSV files in {RAW_DIR}")


if __name__ == "__main__":
    main()
