"""Load real CDC/ATSDR Social Vulnerability Index 2022 data into the community health dataset."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from dotenv import load_dotenv
from pydomo import Domo

load_dotenv(Path(__file__).parent.parent / ".env")

# Path to raw SVI CSV
RAW_CSV = Path(__file__).parent.parent / "data" / "raw" / "SVI_2022_US_county.csv"


def main() -> None:
    client_id = os.environ["DOMO_CLIENT_ID"]
    client_secret = os.environ["DOMO_CLIENT_SECRET"]
    community_id = os.environ["HP_COMMUNITY_DATASET_ID"]

    print(f"Reading SVI data from {RAW_CSV} ...")
    df = pd.read_csv(RAW_CSV, dtype={"FIPS": str, "STCNTY": str})
    print(f"  {len(df)} rows, {len(df.columns)} columns")

    # Extract and rename key columns
    keep = {
        "FIPS": "county_fips",
        "RPL_THEMES": "svi_score",
        "EP_POV150": "poverty_rate",
        "EP_UNEMP": "unemployment_rate",
        "EP_UNINSUR": "uninsured_rate",
        "EP_NOHSDP": "no_diploma_rate",
        "EP_MINRTY": "minority_pct",
        "E_TOTPOP": "total_population",
        "ST_ABBR": "state",
        "COUNTY": "county_name",
    }

    missing = [c for c in keep if c not in df.columns]
    if missing:
        print(f"WARNING: columns not found in CSV, will be filled with NaN: {missing}")

    community = df[[c for c in keep if c in df.columns]].rename(
        columns={c: keep[c] for c in keep if c in df.columns}
    )

    # Ensure county_fips is zero-padded to 5 digits
    community["county_fips"] = community["county_fips"].astype(str).str.zfill(5)

    # RPL_THEMES uses -999 as a sentinel for "no data"; replace with NaN
    if "svi_score" in community.columns:
        community["svi_score"] = pd.to_numeric(community["svi_score"], errors="coerce")
        community.loc[community["svi_score"] < 0, "svi_score"] = None

    # Same sentinel treatment for rate columns
    rate_cols = ["poverty_rate", "unemployment_rate", "uninsured_rate",
                 "no_diploma_rate", "minority_pct"]
    for col in rate_cols:
        if col in community.columns:
            community[col] = pd.to_numeric(community[col], errors="coerce")
            community.loc[community[col] < 0, col] = None

    if "total_population" in community.columns:
        community["total_population"] = pd.to_numeric(
            community["total_population"], errors="coerce"
        ).astype("Int64")

    # Drop rows where both county_fips and svi_score are missing
    before = len(community)
    community = community.dropna(subset=["county_fips"])
    community = community[community["county_fips"].str.len() == 5]
    after = len(community)
    print(f"  Rows after FIPS validation: {after} (dropped {before - after})")

    # Print summary stats
    print("\n--- Summary Statistics ---")
    if "svi_score" in community.columns:
        valid_svi = community["svi_score"].dropna()
        print(f"  SVI score (RPL_THEMES): {len(valid_svi)} valid values")
        print(f"    min={valid_svi.min():.3f}, mean={valid_svi.mean():.3f}, max={valid_svi.max():.3f}")
        high_vuln = (valid_svi >= 0.75).sum()
        print(f"    High vulnerability (SVI >= 0.75): {high_vuln} counties ({high_vuln*100//len(valid_svi)}%)")
    if "poverty_rate" in community.columns:
        pr = community["poverty_rate"].dropna()
        print(f"  Poverty rate (EP_POV150): mean={pr.mean():.1f}%, max={pr.max():.1f}%")
    if "uninsured_rate" in community.columns:
        ur = community["uninsured_rate"].dropna()
        print(f"  Uninsured rate (EP_UNINSUR): mean={ur.mean():.1f}%, max={ur.max():.1f}%")
    if "minority_pct" in community.columns:
        mp = community["minority_pct"].dropna()
        print(f"  Minority % (EP_MINRTY): mean={mp.mean():.1f}%, max={mp.max():.1f}%")
    if "state" in community.columns:
        print(f"  States covered: {community['state'].nunique()}")
    print(f"  Total counties: {len(community)}")

    # Upload to Domo
    print(f"\nConnecting to Domo (instance: {os.environ.get('DOMO_INSTANCE', 'unknown')}) ...")
    domo = Domo(client_id, client_secret, api_host="api.domo.com")

    print(f"Updating HP_COMMUNITY_DATASET_ID={community_id} with real SVI data ...")
    domo.ds_update(community_id, community)
    print("  Done — community dataset updated with real CDC SVI 2022 data.")
    print(f"\nLoaded {len(community)} counties with real SVI scores into dataset {community_id}.")


if __name__ == "__main__":
    main()
