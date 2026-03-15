"""Verify Domo datasets are queryable and have expected row counts."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

EXPECTED_DATASETS = {
    "HP_FACILITIES_DATASET_ID": ("hp_facilities", 4000, 6000),
    "HP_QUALITY_DATASET_ID": ("hp_quality_measures", 30000, 60000),
    "HP_READMISSIONS_DATASET_ID": ("hp_readmissions", 15000, 30000),
    "HP_SAFETY_DATASET_ID": ("hp_safety", 10000, 25000),
    "HP_EXPERIENCE_DATASET_ID": ("hp_patient_experience", 20000, 40000),
    "HP_COST_DATASET_ID": ("hp_cost_efficiency", 3000, 12000),
}


def main() -> None:
    try:
        from pydomo import Domo
    except ImportError:
        print("PyDomo not installed. Checking local CSV files instead.")
        import pandas as pd
        curated_dir = Path(__file__).parent.parent / "data" / "curated"
        for env_key, (name, min_rows, max_rows) in EXPECTED_DATASETS.items():
            path = curated_dir / f"{name}.csv"
            if path.exists():
                df = pd.read_csv(path)
                status = "OK" if min_rows <= len(df) <= max_rows else "WARN"
                print(f"  [{status}] {name}: {len(df)} rows (expected {min_rows}-{max_rows})")
            else:
                print(f"  [MISSING] {name}: file not found")
        return

    client_id = os.environ.get("DOMO_CLIENT_ID")
    client_secret = os.environ.get("DOMO_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("No Domo credentials set. Set DOMO_CLIENT_ID and DOMO_CLIENT_SECRET in .env")
        return

    from pydomo import Domo
    domo = Domo(client_id, client_secret, api_host="api.domo.com")

    all_ok = True
    for env_key, (name, min_rows, max_rows) in EXPECTED_DATASETS.items():
        dataset_id = os.environ.get(env_key)
        if not dataset_id:
            print(f"  [SKIP] {name}: {env_key} not set")
            continue
        try:
            meta = domo.ds_meta(dataset_id)
            row_count = meta.get("rows", 0)
            status = "OK" if min_rows <= row_count <= max_rows else "WARN"
            print(f"  [{status}] {name}: {row_count} rows (expected {min_rows}-{max_rows})")
            if status == "WARN":
                all_ok = False
        except Exception as e:
            print(f"  [ERROR] {name}: {e}")
            all_ok = False

    print(f"\n{'All datasets OK' if all_ok else 'Some datasets need attention'}")


if __name__ == "__main__":
    main()
