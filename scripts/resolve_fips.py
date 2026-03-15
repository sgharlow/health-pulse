"""Resolve county names to FIPS codes using Census Bureau crosswalk."""

import csv
import re
from pathlib import Path
from typing import Optional

import requests

REFERENCE_DIR = Path(__file__).parent.parent / "data" / "reference"
CROSSWALK_PATH = REFERENCE_DIR / "county_fips_crosswalk.csv"

CENSUS_URL = "https://www2.census.gov/geo/docs/reference/codes2020/national_county2020.txt"


def download_crosswalk() -> None:
    """Download Census Bureau county FIPS crosswalk."""
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    if CROSSWALK_PATH.exists():
        print("FIPS crosswalk already exists, skipping download")
        return

    print("Downloading Census Bureau county FIPS crosswalk...")
    resp = requests.get(CENSUS_URL, timeout=30)
    resp.raise_for_status()

    rows = []
    for line in resp.text.strip().split("\n"):
        parts = line.split("|")
        if len(parts) >= 4:
            state_abbrev = parts[0].strip()
            state_fips = parts[1].strip()
            county_fips_suffix = parts[2].strip()
            county_name = parts[3].strip()
            fips_code = state_fips + county_fips_suffix
            rows.append({
                "state": state_abbrev,
                "county_name": county_name,
                "county_fips": fips_code,
            })

    with open(CROSSWALK_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["state", "county_name", "county_fips"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} county entries to {CROSSWALK_PATH}")


def normalize_county(name: str) -> str:
    """Normalize county name for matching."""
    name = name.upper().strip()
    for suffix in [" COUNTY", " PARISH", " BOROUGH", " CENSUS AREA",
                   " MUNICIPALITY", " CITY AND BOROUGH"]:
        name = name.replace(suffix, "")
    name = re.sub(r"\bST\.\s*", "SAINT ", name)
    name = re.sub(r"\bSTE\.\s*", "SAINTE ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def load_crosswalk() -> dict[tuple[str, str], str]:
    """Load crosswalk into a lookup dict: (state, normalized_county) -> fips."""
    if not CROSSWALK_PATH.exists():
        download_crosswalk()

    lookup = {}
    with open(CROSSWALK_PATH) as f:
        for row in csv.DictReader(f):
            key = (row["state"], normalize_county(row["county_name"]))
            lookup[key] = row["county_fips"]
    return lookup


def resolve_fips(state: str, county_name: str,
                 lookup: dict[tuple[str, str], str]) -> Optional[str]:
    """Resolve a (state, county_name) pair to a FIPS code."""
    key = (state.upper().strip(), normalize_county(county_name))
    return lookup.get(key)
