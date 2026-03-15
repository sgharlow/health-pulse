"""Clean CMS CSV data and upload to Domo as curated datasets."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from dotenv import load_dotenv

from resolve_fips import load_crosswalk, resolve_fips

load_dotenv(Path(__file__).parent.parent / ".env")

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

MORTALITY_MEASURES = [
    "MORT_30_AMI", "MORT_30_HF", "MORT_30_COPD", "MORT_30_PN",
    "MORT_30_STK", "MORT_30_CABG", "PSI_90_SAFETY",
]
TIMELY_MEASURES = [
    "OP_18b", "OP_22", "SEP_1", "IMM_3",
    "STK_1", "STK_2", "STK_3", "STK_4", "STK_5", "STK_6",
]
READM_30_PREFIX = "READM_30"
HCAHPS_COMPOSITES = ("_COMP", "_LINEAR", "_STAR", "_RATING")


def _is_hcahps_composite(measure_id: str) -> bool:
    """Return True if the measure ID is a composite measure.

    _COMP matches as a substring (e.g. H_COMP_1_A_P contains _COMP);
    the remaining suffixes are matched with endswith.
    """
    if not measure_id:
        return False
    if "_COMP" in measure_id:
        return True
    return any(measure_id.endswith(s) for s in HCAHPS_COMPOSITES[1:])


def clean_facilities(fips_lookup: dict) -> pd.DataFrame:
    """Load and clean Hospital General Information."""
    path = RAW_DIR / "Hospital_General_Information.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str)
    df["county_fips"] = df.apply(
        lambda r: resolve_fips(r.get("state", ""), r.get("countyparish", ""), fips_lookup),
        axis=1,
    )
    cols = ["facility_id", "facility_name", "address", "citytown", "state",
            "zip_code", "countyparish", "county_fips", "hospital_type",
            "hospital_ownership", "emergency_services", "hospital_overall_rating"]
    return df[[c for c in cols if c in df.columns]]


def clean_quality_measures() -> pd.DataFrame:
    """Merge Complications/Deaths + Timely/Effective Care, filter to key measures."""
    frames = []
    path = RAW_DIR / "Complications_and_Deaths-Hospital.csv"
    if path.exists():
        df = pd.read_csv(path, dtype=str)
        df = df[df["measure_id"].isin(MORTALITY_MEASURES)]
        df = df[df["score"] != "Not Available"]
        frames.append(df[["facility_id", "measure_id", "measure_name", "score",
                          "compared_to_national", "denominator", "start_date", "end_date"]])
    path = RAW_DIR / "Timely_and_Effective_Care-Hospital.csv"
    if path.exists():
        df = pd.read_csv(path, dtype=str)
        df = df[df["measure_id"].isin(TIMELY_MEASURES)]
        df = df[df["score"] != "Not Available"]
        rename = {"_condition": "compared_to_national"} if "_condition" in df.columns else {}
        df = df.rename(columns=rename)
        cols = ["facility_id", "measure_id", "measure_name", "score",
                "compared_to_national", "sample", "start_date", "end_date"]
        frames.append(df[[c for c in cols if c in df.columns]])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def clean_readmissions() -> pd.DataFrame:
    """Merge HRRP + Unplanned Visits, filter to readmission measures."""
    frames = []
    path = RAW_DIR / "FY_2026_Hospital_Readmissions_Reduction_Program_Hospital.csv"
    if path.exists():
        df = pd.read_csv(path, dtype=str)
        cols = ["facility_name", "facility_id", "state", "measure_name",
                "number_of_discharges", "excess_readmission_ratio",
                "predicted_readmission_rate", "expected_readmission_rate",
                "number_of_readmissions", "start_date", "end_date"]
        frames.append(df[[c for c in cols if c in df.columns]])
    path = RAW_DIR / "Unplanned_Hospital_Visits-Hospital.csv"
    if path.exists():
        df = pd.read_csv(path, dtype=str)
        df = df[df["measure_id"].str.startswith(READM_30_PREFIX, na=False)]
        cols = ["facility_id", "measure_id", "measure_name", "score",
                "compared_to_national", "denominator", "start_date", "end_date"]
        frames.append(df[[c for c in cols if c in df.columns]])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def clean_safety() -> pd.DataFrame:
    """Merge HAC Reduction + HAI, filter to SIR/Z-score measures."""
    frames = []
    path = RAW_DIR / "FY_2026_HAC_Reduction_Program_Hospital.csv"
    if path.exists():
        df = pd.read_csv(path, dtype=str)
        frames.append(df)
    path = RAW_DIR / "Healthcare_Associated_Infections-Hospital.csv"
    if path.exists():
        df = pd.read_csv(path, dtype=str)
        df = df[df["measure_id"].str.contains("SIR", na=False)]
        frames.append(df[["facility_id", "measure_id", "measure_name", "score",
                          "compared_to_national", "start_date", "end_date"]])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def clean_patient_experience() -> pd.DataFrame:
    """Filter HCAHPS to composite measures only."""
    path = RAW_DIR / "HCAHPS-Hospital.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str)
    mask = df["hcahps_measure_id"].apply(
        lambda x: _is_hcahps_composite(x) if pd.notna(x) else False
    )
    df = df[mask]
    cols = ["facility_id", "hcahps_measure_id", "hcahps_question",
            "patient_survey_star_rating", "hcahps_answer_percent",
            "number_of_completed_surveys", "start_date", "end_date"]
    return df[[c for c in cols if c in df.columns]]


def clean_cost_efficiency() -> pd.DataFrame:
    """Load MSPB hospital-level data."""
    path = RAW_DIR / "Medicare_Hospital_Spending_Per_Patient-Hospital.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str)
    cols = ["facility_id", "facility_name", "state", "measure_id",
            "measure_name", "score", "start_date", "end_date"]
    return df[[c for c in cols if c in df.columns]]


def upload_to_domo(df: pd.DataFrame, name: str, description: str) -> str:
    """Upload a DataFrame to Domo. Returns dataset ID."""
    try:
        from pydomo import Domo
    except ImportError:
        print(f"  PyDomo not installed. Saving {name} as CSV instead.")
        out = RAW_DIR.parent / "curated" / f"{name}.csv"
        out.parent.mkdir(exist_ok=True)
        df.to_csv(out, index=False)
        print(f"  Saved {len(df)} rows to {out}")
        return f"local:{name}"

    client_id = os.environ.get("DOMO_CLIENT_ID")
    client_secret = os.environ.get("DOMO_CLIENT_SECRET")
    if not client_id or not client_secret:
        print(f"  No Domo credentials. Saving {name} as CSV.")
        out = RAW_DIR.parent / "curated" / f"{name}.csv"
        out.parent.mkdir(exist_ok=True)
        df.to_csv(out, index=False)
        return f"local:{name}"

    domo = Domo(client_id, client_secret, api_host="api.domo.com")
    dataset_id = domo.ds_create(df, name, description)
    print(f"  Uploaded {len(df)} rows -> Domo dataset {dataset_id}")
    return dataset_id


def main() -> None:
    print("Loading FIPS crosswalk...")
    fips_lookup = load_crosswalk()
    print(f"  {len(fips_lookup)} counties loaded")

    datasets = {
        "hp_facilities": ("Hospital facility profiles with FIPS codes",
                          lambda: clean_facilities(fips_lookup)),
        "hp_quality_measures": ("Mortality + process quality measures",
                                clean_quality_measures),
        "hp_readmissions": ("Readmission rates and excess ratios",
                            clean_readmissions),
        "hp_safety": ("HAC + HAI safety measures with SIR/Z-scores",
                      clean_safety),
        "hp_patient_experience": ("HCAHPS composite measures",
                                   clean_patient_experience),
        "hp_cost_efficiency": ("Medicare spending per beneficiary",
                                clean_cost_efficiency),
    }

    results = {}
    for name, (desc, cleaner) in datasets.items():
        print(f"\nProcessing {name}...")
        df = cleaner()
        if df.empty:
            print(f"  WARNING: {name} produced 0 rows (source CSV missing?)")
            continue
        print(f"  {len(df)} rows, {len(df.columns)} columns")
        dataset_id = upload_to_domo(df, name, desc)
        results[name] = dataset_id

    print("\n=== Dataset IDs (add to .env) ===")
    env_map = {
        "hp_facilities": "HP_FACILITIES_DATASET_ID",
        "hp_quality_measures": "HP_QUALITY_DATASET_ID",
        "hp_readmissions": "HP_READMISSIONS_DATASET_ID",
        "hp_safety": "HP_SAFETY_DATASET_ID",
        "hp_patient_experience": "HP_EXPERIENCE_DATASET_ID",
        "hp_cost_efficiency": "HP_COST_DATASET_ID",
    }
    for name, ds_id in results.items():
        env_key = env_map.get(name, name.upper() + "_DATASET_ID")
        print(f"{env_key}={ds_id}")


if __name__ == "__main__":
    main()
