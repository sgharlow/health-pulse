"""Fix FIPS codes in facilities dataset and create community health proxy."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from dotenv import load_dotenv
from pydomo import Domo

from resolve_fips import load_crosswalk, resolve_fips

load_dotenv(Path(__file__).parent.parent / ".env")


def main() -> None:
    client_id = os.environ["DOMO_CLIENT_ID"]
    client_secret = os.environ["DOMO_CLIENT_SECRET"]
    domo = Domo(client_id, client_secret, api_host="api.domo.com")

    fac_id = os.environ["HP_FACILITIES_DATASET_ID"]

    # Step 1: Download facilities from Domo
    print("Downloading facilities from Domo...")
    fac_df = domo.ds_get(fac_id)
    print(f"  {len(fac_df)} facilities")

    # Step 2: Re-resolve FIPS codes using the correct crosswalk
    print("Resolving FIPS codes...")
    fips_lookup = load_crosswalk()
    print(f"  {len(fips_lookup)} counties in crosswalk")

    fac_df["county_fips"] = fac_df.apply(
        lambda r: resolve_fips(
            str(r.get("state", "")),
            str(r.get("county_parish", "")),
            fips_lookup,
        ) or "",
        axis=1,
    )
    resolved = fac_df["county_fips"].str.len() > 0
    total = len(fac_df)
    n_resolved = resolved.sum()
    pct = n_resolved * 100 // total if total else 0
    print(f"  Resolved {n_resolved} of {total} ({pct}%)")

    # Step 3: Update facilities in Domo
    print("Updating facilities dataset in Domo...")
    domo.ds_update(fac_id, fac_df)
    print("  Done")

    # Step 4: Build community health proxy from facilities data
    print("Creating community health dataset...")
    fac_with_fips = fac_df[fac_df["county_fips"].str.len() > 0].copy()

    # Convert star rating to numeric, treating 'Not Available' as NaN
    fac_with_fips["rating_num"] = pd.to_numeric(
        fac_with_fips["hospital_overall_rating"], errors="coerce"
    )

    # Group by county FIPS
    community = (
        fac_with_fips.groupby("county_fips")
        .agg(
            facility_count=("facility_id", "count"),
            avg_star_rating=("rating_num", "mean"),
            min_star_rating=("rating_num", "min"),
            max_star_rating=("rating_num", "max"),
            state=("state", "first"),
            county_name=("county_parish", "first"),
        )
        .reset_index()
    )

    # SVI proxy: counties with lower avg star ratings treated as higher vulnerability
    # Normalised to 0-1 where 1 = most vulnerable
    min_r = community["avg_star_rating"].min()
    max_r = community["avg_star_rating"].max()
    if max_r > min_r:
        community["svi_score"] = (
            1 - (community["avg_star_rating"] - min_r) / (max_r - min_r)
        ).round(3)
    else:
        community["svi_score"] = 0.5

    # Fill NaN svi_score (counties where all facilities have no star rating)
    community["svi_score"] = community["svi_score"].fillna(0.5)

    # Placeholder columns expected by equity_detector
    community["uninsured_rate"] = 0.0
    community["poverty_rate"] = 0.0

    print(f"  {len(community)} counties with community health data")

    # Step 5: Upload community health dataset to Domo
    print("Uploading community health dataset to Domo...")
    comm_id = domo.ds_create(
        community,
        "hp_community_health",
        "Community health metrics by county (SVI proxy derived from CMS facility star ratings)",
    )
    print(f"  HP_COMMUNITY_DATASET_ID={comm_id}")

    print("\nDone! Add to .env:")
    print(f"HP_COMMUNITY_DATASET_ID={comm_id}")


if __name__ == "__main__":
    main()
