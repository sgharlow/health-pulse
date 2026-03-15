# HealthPulse AI Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a healthcare performance intelligence MCP server using real CMS data in Domo, published to Prompt Opinion Marketplace for the Agents Assemble hackathon.

**Architecture:** Python MCP server wraps Domo API with 5 analytics tools (quality monitor, care gap finder, equity detector, facility benchmark, executive briefing) + SHARP context propagation. Data pipeline loads real CMS public hospital data into Domo. Supplementary Next.js dashboard for development/demo.

**Tech Stack:** Python 3.11+ (MCP server, data pipeline), Next.js 16 + TypeScript (dashboard), Domo API + PyDomo (data), pytest + Vitest (testing), HAPI FHIR + Synthea (Phase 2)

**Spec:** `docs/superpowers/specs/2026-03-14-healthpulse-ai-design.md`

---

## Chunk 1: Project Scaffolding + Data Pipeline

### Task 1: Initialize Project Structure

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `CLAUDE.md`
- Create: `mcp-server/pyproject.toml`
- Create: `mcp-server/src/healthpulse_mcp/__init__.py`
- Create: `scripts/requirements.txt`

- [ ] **Step 1: Create .gitignore**

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/
*.egg-info/
dist/
build/

# Node
node_modules/
.next/
out/

# Environment
.env
.env.local
.env.*.local

# Data
data/raw/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Create .env.example**

```env
# Domo Developer Trial
DOMO_CLIENT_ID=
DOMO_CLIENT_SECRET=
DOMO_INSTANCE=

# Anthropic (dashboard only, NOT in MCP server)
ANTHROPIC_API_KEY=

# Dataset IDs (populated after load_cms_data.py runs)
HP_FACILITIES_DATASET_ID=
HP_QUALITY_DATASET_ID=
HP_READMISSIONS_DATASET_ID=
HP_SAFETY_DATASET_ID=
HP_EXPERIENCE_DATASET_ID=
HP_COST_DATASET_ID=
HP_COMMUNITY_DATASET_ID=
```

- [ ] **Step 3: Create CLAUDE.md**

```markdown
# HealthPulse AI

Healthcare performance intelligence MCP server for the Agents Assemble hackathon.

## Architecture
- `mcp-server/` — Python MCP server (primary deliverable)
- `scripts/` — Data pipeline (CMS → Domo)
- `web/` — Next.js dashboard (supplementary)
- `data/raw/` — Downloaded CMS CSVs (gitignored)
- `data/reference/` — Census FIPS crosswalk (committed)

## Commands
- MCP server: `cd mcp-server && pip install -e . && python -m healthpulse_mcp.server`
- Tests (MCP): `cd mcp-server && pytest`
- Data load: `cd scripts && python load_cms_data.py`
- Dashboard: `cd web && npm install && npm run dev`
- Tests (web): `cd web && npm test`

## Key Constraints
- Domo SQL: `FROM table` (literal), use `<>` not `!=`, no JOINs/subqueries
- SHARP headers: X-FHIR-Server-URL, X-Patient-ID, X-FHIR-Access-Token
- No PHI — CMS data is de-identified aggregate, Synthea is synthetic
- MCP server must NOT call Claude — returns structured data for platform LLM
```

- [ ] **Step 4: Create mcp-server/pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "healthpulse-mcp"
version = "0.1.0"
description = "Healthcare performance intelligence MCP server"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "responses>=0.25.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 5: Create mcp-server/src/healthpulse_mcp/__init__.py**

```python
"""HealthPulse AI — Healthcare Performance Intelligence MCP Server."""
```

- [ ] **Step 6: Create scripts/requirements.txt**

```
pandas>=2.2.0
pydomo>=0.3.0
requests>=2.31.0
python-dotenv>=1.0.0
```

- [ ] **Step 7: Create data directories**

Run: `mkdir -p data/raw data/reference`

- [ ] **Step 8: Commit**

```bash
git add .gitignore .env.example CLAUDE.md mcp-server/pyproject.toml mcp-server/src/healthpulse_mcp/__init__.py scripts/requirements.txt
git commit -m "chore: initialize HealthPulse AI project structure"
```

---

### Task 2: CMS Data Download Script

**Files:**
- Create: `scripts/download_cms_data.py`
- Test: `scripts/test_download.py`

- [ ] **Step 1: Write download_cms_data.py**

```python
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
```

- [ ] **Step 2: Write test_download.py**

```python
"""Smoke test for CMS dataset configuration."""

from download_cms_data import CMS_DATASETS


def test_all_datasets_have_required_fields():
    for name, info in CMS_DATASETS.items():
        assert "id" in info, f"{name} missing dataset id"
        assert "filename" in info, f"{name} missing filename"
        assert info["filename"].endswith(".csv"), f"{name} filename must end in .csv"


def test_dataset_count():
    assert len(CMS_DATASETS) == 9
```

- [ ] **Step 3: Run test**

Run: `cd scripts && python -m pytest test_download.py -v`
Expected: 2 tests PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/download_cms_data.py scripts/test_download.py
git commit -m "feat: add CMS data download script"
```

---

### Task 3: FIPS Code Resolution

**Files:**
- Create: `scripts/resolve_fips.py`
- Create: `scripts/test_resolve_fips.py`

- [ ] **Step 1: Write resolve_fips.py**

This script downloads the Census Bureau county FIPS crosswalk and provides a function to map (state, county_name) → FIPS code.

```python
"""Resolve county names to FIPS codes using Census Bureau crosswalk."""

import csv
import re
from pathlib import Path
from typing import Optional

import requests

REFERENCE_DIR = Path(__file__).parent.parent / "data" / "reference"
CROSSWALK_PATH = REFERENCE_DIR / "county_fips_crosswalk.csv"

# Census Bureau National County file
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
    # Remove common suffixes
    for suffix in [" COUNTY", " PARISH", " BOROUGH", " CENSUS AREA",
                   " MUNICIPALITY", " CITY AND BOROUGH"]:
        name = name.replace(suffix, "")
    # Normalize Saint variants
    name = re.sub(r"\bST\.\s*", "SAINT ", name)
    name = re.sub(r"\bSTE\.\s*", "SAINTE ", name)
    # Collapse whitespace
    name = re.sub(r"\s+", " ", name).strip()
    return name


def load_crosswalk() -> dict[tuple[str, str], str]:
    """Load crosswalk into a lookup dict: (state, normalized_county) → fips."""
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
```

- [ ] **Step 2: Write test_resolve_fips.py**

```python
"""Tests for FIPS code resolution."""

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
```

- [ ] **Step 3: Run tests**

Run: `cd scripts && python -m pytest test_resolve_fips.py -v`
Expected: 6 tests PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/resolve_fips.py scripts/test_resolve_fips.py
git commit -m "feat: add county FIPS code resolution with Census crosswalk"
```

---

### Task 4: CMS Data Cleaning + Domo Upload Script

**Files:**
- Create: `scripts/load_cms_data.py`
- Create: `scripts/test_load_cms_data.py`

- [ ] **Step 1: Write load_cms_data.py**

```python
"""Clean CMS CSV data and upload to Domo as curated datasets."""

import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from resolve_fips import load_crosswalk, resolve_fips

load_dotenv(Path(__file__).parent.parent / ".env")

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

# Measure IDs to keep (from spec section 4.3.1)
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


def clean_facilities(fips_lookup: dict) -> pd.DataFrame:
    """Load and clean Hospital General Information."""
    path = RAW_DIR / "Hospital_General_Information.csv"
    df = pd.read_csv(path, dtype=str)
    # Add FIPS code
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

    # Complications & Deaths
    path = RAW_DIR / "Complications_and_Deaths-Hospital.csv"
    if path.exists():
        df = pd.read_csv(path, dtype=str)
        df = df[df["measure_id"].isin(MORTALITY_MEASURES)]
        df = df[df["score"] != "Not Available"]
        frames.append(df[["facility_id", "measure_id", "measure_name", "score",
                          "compared_to_national", "denominator", "start_date", "end_date"]])

    # Timely & Effective Care
    path = RAW_DIR / "Timely_and_Effective_Care-Hospital.csv"
    if path.exists():
        df = pd.read_csv(path, dtype=str)
        df = df[df["measure_id"].isin(TIMELY_MEASURES)]
        df = df[df["score"] != "Not Available"]
        # Rename '_condition' to align schema
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
        frames.append(df[["facility_name", "facility_id", "state", "measure_name",
                          "number_of_discharges", "excess_readmission_ratio",
                          "predicted_readmission_rate", "expected_readmission_rate",
                          "number_of_readmissions", "start_date", "end_date"]])

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
        lambda x: any(x.endswith(s) for s in HCAHPS_COMPOSITES) if pd.notna(x) else False
    )
    df = df[mask]
    return df[["facility_id", "hcahps_measure_id", "hcahps_question",
               "patient_survey_star_rating", "hcahps_answer_percent",
               "number_of_completed_surveys", "start_date", "end_date"]]


def clean_cost_efficiency() -> pd.DataFrame:
    """Load MSPB hospital-level data."""
    path = RAW_DIR / "Medicare_Hospital_Spending_Per_Patient-Hospital.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str)
    return df[["facility_id", "facility_name", "state", "measure_id",
               "measure_name", "score", "start_date", "end_date"]]


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
    print(f"  Uploaded {len(df)} rows → Domo dataset {dataset_id}")
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
```

- [ ] **Step 2: Write test_load_cms_data.py**

```python
"""Tests for CMS data cleaning logic (no Domo dependency)."""

import pandas as pd

from load_cms_data import (
    MORTALITY_MEASURES, TIMELY_MEASURES, HCAHPS_COMPOSITES,
    READM_30_PREFIX,
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
    kept = [x for x in test_ids if any(x.endswith(s) for s in HCAHPS_COMPOSITES)]
    assert "H_COMP_1" in kept
    assert "H_CLEAN_LINEAR" in kept
    assert "H_STAR_RATING" in kept
    assert "H_QUIET_HSP_A_P" not in kept
```

- [ ] **Step 3: Run tests**

Run: `cd scripts && python -m pytest test_load_cms_data.py -v`
Expected: 4 tests PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/load_cms_data.py scripts/test_load_cms_data.py
git commit -m "feat: add CMS data cleaning and Domo upload pipeline"
```

---

### Task 5: Verify Datasets Script

**Files:**
- Create: `scripts/verify_datasets.py`

- [ ] **Step 1: Write verify_datasets.py**

```python
"""Verify Domo datasets are queryable and have expected row counts."""

import os
from pathlib import Path

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
        curated_dir = Path(__file__).parent.parent / "data" / "curated"
        for env_key, (name, min_rows, max_rows) in EXPECTED_DATASETS.items():
            path = curated_dir / f"{name}.csv"
            if path.exists():
                import pandas as pd
                df = pd.read_csv(path)
                status = "OK" if min_rows <= len(df) <= max_rows else "WARN"
                print(f"  [{status}] {name}: {len(df)} rows (expected {min_rows}-{max_rows})")
            else:
                print(f"  [MISSING] {name}: file not found")
        return

    client_id = os.environ["DOMO_CLIENT_ID"]
    client_secret = os.environ["DOMO_CLIENT_SECRET"]
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
```

- [ ] **Step 2: Commit**

```bash
git add scripts/verify_datasets.py
git commit -m "feat: add dataset verification script"
```

---

## Chunk 2: MCP Server Core (Domo Client + Analytics + SHARP)

### Task 6: Domo API Client

**Files:**
- Create: `mcp-server/src/healthpulse_mcp/domo_client.py`
- Create: `mcp-server/tests/test_domo_client.py`

- [ ] **Step 1: Write failing test for token acquisition**

```python
"""Tests for Domo API client."""

import responses
import pytest
from healthpulse_mcp.domo_client import DomoClient


@responses.activate
def test_get_token_uses_get_request():
    """Domo OAuth uses GET (not POST) — non-standard."""
    responses.add(
        responses.GET,
        "https://api.domo.com/oauth/token",
        json={"access_token": "test-token", "token_type": "bearer", "expires_in": 3600},
    )
    client = DomoClient("test-id", "test-secret")
    token = client.get_token()
    assert token == "test-token"
    assert responses.calls[0].request.method == "GET"


@responses.activate
def test_token_caching():
    """Token should be cached and not re-fetched within TTL."""
    responses.add(
        responses.GET,
        "https://api.domo.com/oauth/token",
        json={"access_token": "cached-token", "token_type": "bearer", "expires_in": 3600},
    )
    client = DomoClient("test-id", "test-secret")
    token1 = client.get_token()
    token2 = client.get_token()
    assert token1 == token2
    assert len(responses.calls) == 1  # Only one HTTP call


@responses.activate
def test_query_dataset():
    """Test SQL query execution against Domo dataset."""
    responses.add(
        responses.GET,
        "https://api.domo.com/oauth/token",
        json={"access_token": "t", "token_type": "bearer", "expires_in": 3600},
    )
    responses.add(
        responses.POST,
        "https://api.domo.com/v1/datasets/query/execute/ds-123",
        json={"columns": ["name", "score"], "rows": [["Hospital A", "12.5"]], "numRows": 1},
    )
    client = DomoClient("test-id", "test-secret")
    result = client.query("ds-123", "SELECT name, score FROM table LIMIT 1")
    assert result["numRows"] == 1
    assert result["columns"] == ["name", "score"]


@responses.activate
def test_query_returns_dicts():
    """Test helper that zips columns + rows into dicts."""
    responses.add(
        responses.GET,
        "https://api.domo.com/oauth/token",
        json={"access_token": "t", "token_type": "bearer", "expires_in": 3600},
    )
    responses.add(
        responses.POST,
        "https://api.domo.com/v1/datasets/query/execute/ds-123",
        json={"columns": ["id", "val"], "rows": [["1", "a"], ["2", "b"]], "numRows": 2},
    )
    client = DomoClient("test-id", "test-secret")
    rows = client.query_as_dicts("ds-123", "SELECT id, val FROM table")
    assert rows == [{"id": "1", "val": "a"}, {"id": "2", "val": "b"}]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd mcp-server && pip install -e ".[dev]" && pytest tests/test_domo_client.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement DomoClient**

```python
"""Domo API client with OAuth token caching and SQL query execution."""

import base64
import time
from typing import Any, Optional

import requests


class DomoClient:
    """Wraps Domo REST API with token caching."""

    API_BASE = "https://api.domo.com"
    TOKEN_BUFFER_SECONDS = 60

    def __init__(self, client_id: str, client_secret: str):
        self._client_id = client_id
        self._client_secret = client_secret
        self._cached_token: Optional[str] = None
        self._token_expires_at: float = 0

    def get_token(self) -> str:
        """Get OAuth token, using cache if valid."""
        now = time.time()
        if self._cached_token and now < self._token_expires_at - self.TOKEN_BUFFER_SECONDS:
            return self._cached_token

        basic = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode()
        ).decode()
        resp = requests.get(
            f"{self.API_BASE}/oauth/token",
            params={"grant_type": "client_credentials", "scope": "data"},
            headers={"Authorization": f"Basic {basic}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._cached_token = data["access_token"]
        self._token_expires_at = now + data.get("expires_in", 3600)
        return self._cached_token

    def query(self, dataset_id: str, sql: str) -> dict[str, Any]:
        """Execute SQL query against a Domo dataset. Returns raw response."""
        token = self.get_token()
        resp = requests.post(
            f"{self.API_BASE}/v1/datasets/query/execute/{dataset_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"sql": sql},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()

    def query_as_dicts(self, dataset_id: str, sql: str) -> list[dict[str, Any]]:
        """Execute SQL and return results as list of dicts."""
        result = self.query(dataset_id, sql)
        columns = result.get("columns", [])
        rows = result.get("rows", [])
        return [dict(zip(columns, row)) for row in rows]

    def get_dataset_info(self, dataset_id: str) -> dict[str, Any]:
        """Get dataset metadata (name, schema, row count)."""
        token = self.get_token()
        resp = requests.get(
            f"{self.API_BASE}/v1/datasets/{dataset_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
```

- [ ] **Step 4: Run tests**

Run: `cd mcp-server && pytest tests/test_domo_client.py -v`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add mcp-server/src/healthpulse_mcp/domo_client.py mcp-server/tests/test_domo_client.py
git commit -m "feat: add Domo API client with OAuth token caching"
```

---

### Task 7: Analytics Engine (Z-Score + Anomaly Detection)

**Files:**
- Create: `mcp-server/src/healthpulse_mcp/analytics.py`
- Create: `mcp-server/tests/test_analytics.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for analytics engine — Z-score and anomaly detection."""

import pytest
from healthpulse_mcp.analytics import (
    compute_z_scores, classify_severity, detect_anomalies,
)


def test_compute_z_scores_basic():
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    z_scores = compute_z_scores(values)
    assert len(z_scores) == 5
    assert abs(z_scores[2]) < 0.01  # Middle value should be ~0


def test_compute_z_scores_with_labels():
    values = [10.0, 20.0, 100.0]
    labels = ["A", "B", "C"]
    results = compute_z_scores(values, labels)
    assert results[2] > 1.0  # Outlier should have high Z


def test_classify_severity_critical():
    assert classify_severity(3.5) == "critical"


def test_classify_severity_high():
    assert classify_severity(2.7) == "high"


def test_classify_severity_medium():
    assert classify_severity(2.1) == "medium"


def test_classify_severity_normal():
    assert classify_severity(1.5) is None


def test_detect_anomalies():
    data = [
        {"facility": "A", "measure": "MORT", "score": 10.0},
        {"facility": "B", "measure": "MORT", "score": 12.0},
        {"facility": "C", "measure": "MORT", "score": 50.0},  # Outlier
    ]
    anomalies = detect_anomalies(data, score_key="score", threshold=2.0)
    assert len(anomalies) == 1
    assert anomalies[0]["facility"] == "C"
    assert anomalies[0]["severity"] in ("medium", "high", "critical")
    assert "z_score" in anomalies[0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd mcp-server && pytest tests/test_analytics.py -v`
Expected: FAIL

- [ ] **Step 3: Implement analytics.py**

```python
"""Z-score computation and anomaly detection for healthcare quality metrics."""

import math
from typing import Any, Optional


def compute_z_scores(
    values: list[float],
    labels: Optional[list[str]] = None,
) -> list[float]:
    """Compute Z-scores for a list of numeric values.

    Returns list of Z-scores in the same order as input values.
    """
    n = len(values)
    if n < 2:
        return [0.0] * n

    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std = math.sqrt(variance) if variance > 0 else 1.0

    return [(x - mean) / std for x in values]


def classify_severity(z_score: float) -> Optional[str]:
    """Classify anomaly severity based on absolute Z-score.

    Returns None if not anomalous (|z| < 2.0).
    """
    abs_z = abs(z_score)
    if abs_z >= 3.0:
        return "critical"
    elif abs_z >= 2.5:
        return "high"
    elif abs_z >= 2.0:
        return "medium"
    return None


def detect_anomalies(
    data: list[dict[str, Any]],
    score_key: str = "score",
    threshold: float = 2.0,
) -> list[dict[str, Any]]:
    """Detect anomalies in a list of facility/measure data.

    Returns list of anomalous entries with z_score and severity added.
    """
    # Extract numeric scores, skip non-numeric
    scored = []
    for item in data:
        try:
            val = float(item[score_key])
            scored.append((item, val))
        except (ValueError, TypeError, KeyError):
            continue

    if len(scored) < 2:
        return []

    values = [v for _, v in scored]
    z_scores = compute_z_scores(values)

    anomalies = []
    for (item, _val), z in zip(scored, z_scores):
        severity = classify_severity(z)
        if severity and abs(z) >= threshold:
            anomalies.append({
                **item,
                "z_score": round(z, 2),
                "severity": severity,
            })

    # Sort by severity (critical first)
    severity_order = {"critical": 0, "high": 1, "medium": 2}
    anomalies.sort(key=lambda x: severity_order.get(x["severity"], 99))
    return anomalies
```

- [ ] **Step 4: Run tests**

Run: `cd mcp-server && pytest tests/test_analytics.py -v`
Expected: 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add mcp-server/src/healthpulse_mcp/analytics.py mcp-server/tests/test_analytics.py
git commit -m "feat: add Z-score anomaly detection engine"
```

---

### Task 8: SHARP Context Propagation

**Files:**
- Create: `mcp-server/src/healthpulse_mcp/sharp.py`
- Create: `mcp-server/tests/test_sharp.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for SHARP healthcare context propagation."""

from healthpulse_mcp.sharp import SharpContext, extract_sharp_context


def test_extract_from_headers():
    headers = {
        "X-FHIR-Server-URL": "https://fhir.example.com/r4",
        "X-Patient-ID": "patient-123",
        "X-FHIR-Access-Token": "bearer-token-abc",
    }
    ctx = extract_sharp_context(headers)
    assert ctx.fhir_server_url == "https://fhir.example.com/r4"
    assert ctx.patient_id == "patient-123"
    assert ctx.fhir_access_token == "bearer-token-abc"
    assert ctx.has_fhir_context is True


def test_extract_empty_headers():
    ctx = extract_sharp_context({})
    assert ctx.fhir_server_url is None
    assert ctx.patient_id is None
    assert ctx.has_fhir_context is False


def test_partial_headers():
    headers = {"X-Patient-ID": "patient-456"}
    ctx = extract_sharp_context(headers)
    assert ctx.patient_id == "patient-456"
    assert ctx.fhir_server_url is None
    assert ctx.has_fhir_context is False  # Need server URL too


def test_token_not_in_repr():
    """SHARP tokens must NEVER appear in logs or string representations."""
    headers = {"X-FHIR-Access-Token": "secret-token"}
    ctx = extract_sharp_context(headers)
    text = repr(ctx)
    assert "secret-token" not in text


def test_sharp_capabilities():
    from healthpulse_mcp.sharp import SHARP_CAPABILITIES
    assert SHARP_CAPABILITIES["experimental"]["fhir_context_required"]["value"] is False
```

- [ ] **Step 2: Run tests to verify fail**

Run: `cd mcp-server && pytest tests/test_sharp.py -v`
Expected: FAIL

- [ ] **Step 3: Implement sharp.py**

```python
"""SHARP Extension Specs — Healthcare context propagation for MCP.

Implements the SHARP-on-MCP spec (https://sharponmcp.com).
Three HTTP headers propagate healthcare context:
  - X-FHIR-Server-URL
  - X-Patient-ID
  - X-FHIR-Access-Token (NEVER logged or passed to LLM)
"""

from dataclasses import dataclass
from typing import Any, Optional


SHARP_CAPABILITIES: dict[str, Any] = {
    "experimental": {
        "fhir_context_required": {"value": False},
    },
}


@dataclass
class SharpContext:
    """Healthcare context extracted from SHARP headers."""

    fhir_server_url: Optional[str] = None
    patient_id: Optional[str] = None
    fhir_access_token: Optional[str] = None

    @property
    def has_fhir_context(self) -> bool:
        """True if both server URL and patient ID are present."""
        return bool(self.fhir_server_url and self.patient_id)

    def __repr__(self) -> str:
        """Safe repr — NEVER include the access token."""
        token_status = "present" if self.fhir_access_token else "absent"
        return (
            f"SharpContext(fhir_server_url={self.fhir_server_url!r}, "
            f"patient_id={self.patient_id!r}, "
            f"fhir_access_token=<{token_status}>)"
        )


def extract_sharp_context(headers: dict[str, str]) -> SharpContext:
    """Extract SHARP context from HTTP headers."""
    return SharpContext(
        fhir_server_url=headers.get("X-FHIR-Server-URL"),
        patient_id=headers.get("X-Patient-ID"),
        fhir_access_token=headers.get("X-FHIR-Access-Token"),
    )
```

- [ ] **Step 4: Run tests**

Run: `cd mcp-server && pytest tests/test_sharp.py -v`
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add mcp-server/src/healthpulse_mcp/sharp.py mcp-server/tests/test_sharp.py
git commit -m "feat: add SHARP healthcare context propagation"
```

---

### Task 9: MCP Server Entry Point

**Files:**
- Create: `mcp-server/src/healthpulse_mcp/server.py`
- Create: `mcp-server/tests/test_server.py`

- [ ] **Step 1: Write server.py**

This is the MCP server entry point. It registers tools, resources, and SHARP capabilities. Individual tool implementations (Tasks 10-14) will be added in subsequent tasks.

```python
"""HealthPulse AI MCP Server — Healthcare Performance Intelligence.

Entry point for the MCP server. Registers tools, resources, and SHARP capabilities.
Published to Prompt Opinion Marketplace.
"""

import os
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent

from healthpulse_mcp.domo_client import DomoClient
from healthpulse_mcp.sharp import SHARP_CAPABILITIES, SharpContext, extract_sharp_context

load_dotenv()

server = Server("healthpulse-ai")

# Global Domo client (initialized on first use)
_domo: DomoClient | None = None


def get_domo() -> DomoClient:
    """Get or create the Domo API client."""
    global _domo
    if _domo is None:
        _domo = DomoClient(
            os.environ["DOMO_CLIENT_ID"],
            os.environ["DOMO_CLIENT_SECRET"],
        )
    return _domo


def get_dataset_id(env_key: str) -> str:
    """Get a dataset ID from environment, raising clear error if missing."""
    value = os.environ.get(env_key)
    if not value:
        raise ValueError(f"Environment variable {env_key} not set. Run scripts/load_cms_data.py first.")
    return value


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available HealthPulse tools."""
    return [
        Tool(
            name="quality_monitor",
            description="Detect healthcare quality anomalies across facilities using Z-score analysis on mortality, readmissions, safety, and timeliness measures.",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {"type": "string", "description": "Optional 2-letter state code to filter"},
                    "measure_group": {"type": "string", "enum": ["mortality", "readmission", "safety", "timeliness", "all"], "default": "all"},
                    "threshold_sigma": {"type": "number", "default": 2.0, "description": "Z-score threshold for anomaly flagging"},
                },
            },
        ),
        Tool(
            name="care_gap_finder",
            description="Identify facilities with excess readmission ratios or worse-than-national mortality.",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {"type": "string", "description": "Optional 2-letter state code to filter"},
                    "gap_type": {"type": "string", "enum": ["readmission", "mortality", "safety", "all"], "default": "all"},
                    "min_excess_ratio": {"type": "number", "default": 1.05},
                },
            },
        ),
        Tool(
            name="equity_detector",
            description="Correlate facility quality outcomes with community social vulnerability (CDC SVI).",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {"type": "string", "description": "Optional 2-letter state code"},
                    "svi_threshold": {"type": "number", "default": 0.75, "description": "SVI percentile threshold (0-1)"},
                    "outcome_measure": {"type": "string", "enum": ["readmission", "mortality", "safety"], "default": "readmission"},
                },
            },
        ),
        Tool(
            name="facility_benchmark",
            description="Compare two or more facilities across all quality dimensions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "facility_ids": {"type": "array", "items": {"type": "string"}, "description": "CMS CCN facility IDs"},
                    "measures": {"type": "array", "items": {"type": "string"}, "default": ["mortality", "readmission", "safety", "patient_experience", "cost"]},
                },
                "required": ["facility_ids"],
            },
        ),
        Tool(
            name="executive_briefing",
            description="Aggregate analytics into structured briefing data for AI narrative generation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "scope": {"type": "string", "enum": ["state", "facility", "network"], "default": "state"},
                    "state": {"type": "string", "description": "For state scope"},
                    "facility_ids": {"type": "array", "items": {"type": "string"}, "description": "For facility/network scope"},
                    "include_equity": {"type": "boolean", "default": True},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Route tool calls to implementations."""
    import json

    # Tool implementations will be imported from tools/ subpackage
    if name == "quality_monitor":
        from healthpulse_mcp.tools.quality_monitor import run
        result = await run(get_domo(), arguments)
    elif name == "care_gap_finder":
        from healthpulse_mcp.tools.care_gap_finder import run
        result = await run(get_domo(), arguments)
    elif name == "equity_detector":
        from healthpulse_mcp.tools.equity_detector import run
        result = await run(get_domo(), arguments)
    elif name == "facility_benchmark":
        from healthpulse_mcp.tools.facility_benchmark import run
        result = await run(get_domo(), arguments)
    elif name == "executive_briefing":
        from healthpulse_mcp.tools.executive_briefing import run
        result = await run(get_domo(), arguments)
    else:
        result = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


def main():
    """Run the MCP server."""
    import asyncio
    from mcp.server.stdio import stdio_server

    async def run_server():
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create tools/__init__.py placeholder**

```python
"""HealthPulse MCP tool implementations."""
```

Save to: `mcp-server/src/healthpulse_mcp/tools/__init__.py`

- [ ] **Step 3: Create resources/__init__.py placeholder**

```python
"""HealthPulse MCP resource implementations."""
```

Save to: `mcp-server/src/healthpulse_mcp/resources/__init__.py`

- [ ] **Step 4: Write test_server.py**

```python
"""Tests for MCP server tool registration."""

import pytest


def test_server_imports():
    """Verify server module can be imported."""
    from healthpulse_mcp.server import server, list_tools
    assert server.name == "healthpulse-ai"


@pytest.mark.asyncio
async def test_list_tools_returns_five():
    from healthpulse_mcp.server import list_tools
    tools = await list_tools()
    assert len(tools) == 5
    names = {t.name for t in tools}
    assert names == {"quality_monitor", "care_gap_finder", "equity_detector",
                     "facility_benchmark", "executive_briefing"}


@pytest.mark.asyncio
async def test_tools_have_input_schemas():
    from healthpulse_mcp.server import list_tools
    tools = await list_tools()
    for tool in tools:
        assert tool.inputSchema is not None
        assert tool.inputSchema["type"] == "object"
```

- [ ] **Step 5: Run tests**

Run: `cd mcp-server && pytest tests/test_server.py -v`
Expected: 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add mcp-server/src/healthpulse_mcp/server.py mcp-server/src/healthpulse_mcp/tools/__init__.py mcp-server/src/healthpulse_mcp/resources/__init__.py mcp-server/tests/test_server.py
git commit -m "feat: add MCP server entry point with 5 tool registrations"
```

---

## Chunk 3: MCP Tool Implementations

### Task 10: Quality Monitor Tool

**Files:**
- Create: `mcp-server/src/healthpulse_mcp/tools/quality_monitor.py`
- Create: `mcp-server/tests/test_quality_monitor.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for quality_monitor tool."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from healthpulse_mcp.tools.quality_monitor import run


@pytest.fixture
def mock_domo():
    client = MagicMock()
    client.query_as_dicts.return_value = [
        {"facility_id": "050001", "facility_name": "Hospital A", "measure_id": "MORT_30_AMI", "score": "12.5", "compared_to_national": "No Different Than the National Rate"},
        {"facility_id": "050002", "facility_name": "Hospital B", "measure_id": "MORT_30_AMI", "score": "25.0", "compared_to_national": "Worse Than the National Rate"},
        {"facility_id": "050003", "facility_name": "Hospital C", "measure_id": "MORT_30_AMI", "score": "10.0", "compared_to_national": "Better Than the National Rate"},
    ]
    return client


@pytest.mark.asyncio
async def test_quality_monitor_returns_anomalies(mock_domo):
    result = await run(mock_domo, {"measure_group": "mortality", "threshold_sigma": 1.5})
    assert "anomalies" in result
    assert isinstance(result["anomalies"], list)


@pytest.mark.asyncio
async def test_quality_monitor_flags_worse_facilities(mock_domo):
    result = await run(mock_domo, {"measure_group": "mortality", "threshold_sigma": 1.0})
    facility_ids = [a["facility_id"] for a in result["anomalies"]]
    assert "050002" in facility_ids  # The outlier with score 25.0


@pytest.mark.asyncio
async def test_quality_monitor_respects_state_filter(mock_domo):
    result = await run(mock_domo, {"state": "CA", "measure_group": "all"})
    # Should have called query with state filter
    call_args = mock_domo.query_as_dicts.call_args
    assert "CA" in str(call_args)
```

- [ ] **Step 2: Implement quality_monitor.py**

```python
"""Quality Monitor — Detect healthcare quality anomalies via Z-score analysis."""

import os
from typing import Any

from healthpulse_mcp.analytics import detect_anomalies
from healthpulse_mcp.domo_client import DomoClient

MEASURE_GROUPS = {
    "mortality": ["MORT_30_AMI", "MORT_30_HF", "MORT_30_COPD", "MORT_30_PN", "MORT_30_STK", "MORT_30_CABG"],
    "safety": ["PSI_90_SAFETY"],
    "timeliness": ["OP_18b", "OP_22", "SEP_1"],
}


async def run(domo: DomoClient, args: dict[str, Any]) -> dict[str, Any]:
    """Run quality monitoring analysis."""
    state = args.get("state")
    group = args.get("measure_group", "all")
    threshold = args.get("threshold_sigma", 2.0)

    dataset_id = os.environ.get("HP_QUALITY_DATASET_ID", "")
    if not dataset_id:
        return {"error": "HP_QUALITY_DATASET_ID not configured"}

    # Build measure filter
    if group == "all":
        measures = [m for ms in MEASURE_GROUPS.values() for m in ms]
    else:
        measures = MEASURE_GROUPS.get(group, [])

    if not measures:
        return {"error": f"Unknown measure group: {group}"}

    measure_list = ", ".join(f"'{m}'" for m in measures)
    where_clauses = [f"measure_id IN ({measure_list})"]
    if state:
        where_clauses.append(f"state = '{state}'")

    where = " AND ".join(where_clauses)
    # Note: Domo SQL uses FROM table (literal)
    sql = f"SELECT facility_id, measure_id, measure_name, score, compared_to_national FROM table WHERE {where}"

    data = domo.query_as_dicts(dataset_id, sql)

    # Run anomaly detection per measure
    all_anomalies = []
    measures_seen = set()
    for row in data:
        measures_seen.add(row.get("measure_id"))

    for measure_id in measures_seen:
        measure_data = [r for r in data if r.get("measure_id") == measure_id]
        anomalies = detect_anomalies(measure_data, score_key="score", threshold=threshold)
        all_anomalies.extend(anomalies)

    return {
        "total_facilities_analyzed": len(data),
        "measures_checked": list(measures_seen),
        "anomaly_count": len(all_anomalies),
        "anomalies": all_anomalies[:20],  # Top 20
        "filters": {"state": state, "measure_group": group, "threshold": threshold},
    }
```

- [ ] **Step 3: Run tests**

Run: `cd mcp-server && pytest tests/test_quality_monitor.py -v`
Expected: 3 tests PASS

- [ ] **Step 4: Commit**

```bash
git add mcp-server/src/healthpulse_mcp/tools/quality_monitor.py mcp-server/tests/test_quality_monitor.py
git commit -m "feat: add quality_monitor MCP tool"
```

---

### Task 11: Care Gap Finder Tool

**Files:**
- Create: `mcp-server/src/healthpulse_mcp/tools/care_gap_finder.py`
- Create: `mcp-server/tests/test_care_gap_finder.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for care_gap_finder tool."""

import pytest
from unittest.mock import MagicMock
from healthpulse_mcp.tools.care_gap_finder import run


@pytest.fixture
def mock_domo():
    client = MagicMock()
    client.query_as_dicts.return_value = [
        {"facility_id": "050001", "facility_name": "Good Hospital", "measure_name": "AMI", "excess_readmission_ratio": "0.95", "number_of_discharges": "500"},
        {"facility_id": "050002", "facility_name": "At-Risk Hospital", "measure_name": "AMI", "excess_readmission_ratio": "1.15", "number_of_discharges": "300"},
        {"facility_id": "050003", "facility_name": "High-Risk Hospital", "measure_name": "AMI", "excess_readmission_ratio": "1.25", "number_of_discharges": "200"},
    ]
    return client


@pytest.mark.asyncio
async def test_finds_gaps_above_threshold(mock_domo):
    result = await run(mock_domo, {"gap_type": "readmission", "min_excess_ratio": 1.05})
    assert len(result["gaps"]) == 2
    ids = [g["facility_id"] for g in result["gaps"]]
    assert "050002" in ids
    assert "050003" in ids


@pytest.mark.asyncio
async def test_excludes_facilities_below_threshold(mock_domo):
    result = await run(mock_domo, {"gap_type": "readmission", "min_excess_ratio": 1.20})
    assert len(result["gaps"]) == 1
    assert result["gaps"][0]["facility_id"] == "050003"


@pytest.mark.asyncio
async def test_sorted_by_excess_ratio_desc(mock_domo):
    result = await run(mock_domo, {"gap_type": "readmission", "min_excess_ratio": 1.0})
    ratios = [float(g["excess_readmission_ratio"]) for g in result["gaps"]]
    assert ratios == sorted(ratios, reverse=True)
```

- [ ] **Step 2: Implement care_gap_finder.py**

```python
"""Care Gap Finder — Identify facilities with excess readmission or mortality gaps."""

import os
from typing import Any

from healthpulse_mcp.domo_client import DomoClient


async def run(domo: DomoClient, args: dict[str, Any]) -> dict[str, Any]:
    """Find care gaps across facilities."""
    state = args.get("state")
    gap_type = args.get("gap_type", "all")
    min_ratio = args.get("min_excess_ratio", 1.05)

    results = {"gaps": [], "filters": {"state": state, "gap_type": gap_type, "min_excess_ratio": min_ratio}}

    if gap_type in ("readmission", "all"):
        dataset_id = os.environ.get("HP_READMISSIONS_DATASET_ID", "")
        if dataset_id:
            where = "excess_readmission_ratio <> 'Not Available'"
            if state:
                where += f" AND state = '{state}'"
            sql = f"SELECT facility_id, facility_name, state, measure_name, excess_readmission_ratio, predicted_readmission_rate, expected_readmission_rate, number_of_discharges FROM table WHERE {where}"
            data = domo.query_as_dicts(dataset_id, sql)

            for row in data:
                try:
                    ratio = float(row.get("excess_readmission_ratio", "0"))
                    if ratio >= min_ratio:
                        results["gaps"].append({**row, "gap_type": "readmission"})
                except (ValueError, TypeError):
                    continue

    if gap_type in ("mortality", "all"):
        dataset_id = os.environ.get("HP_QUALITY_DATASET_ID", "")
        if dataset_id:
            where = "compared_to_national = 'Worse Than the National Rate'"
            if state:
                where += f" AND state = '{state}'"
            sql = f"SELECT facility_id, measure_id, measure_name, score, compared_to_national FROM table WHERE {where}"
            data = domo.query_as_dicts(dataset_id, sql)
            for row in data:
                results["gaps"].append({**row, "gap_type": "mortality"})

    # Sort by excess ratio descending (readmission gaps first)
    results["gaps"].sort(
        key=lambda g: float(g.get("excess_readmission_ratio", "0")),
        reverse=True,
    )
    results["total_gaps"] = len(results["gaps"])
    results["gaps"] = results["gaps"][:30]  # Top 30
    return results
```

- [ ] **Step 3: Run tests**

Run: `cd mcp-server && pytest tests/test_care_gap_finder.py -v`
Expected: 3 tests PASS

- [ ] **Step 4: Commit**

```bash
git add mcp-server/src/healthpulse_mcp/tools/care_gap_finder.py mcp-server/tests/test_care_gap_finder.py
git commit -m "feat: add care_gap_finder MCP tool"
```

---

### Task 12: Equity Detector Tool

**Files:**
- Create: `mcp-server/src/healthpulse_mcp/tools/equity_detector.py`
- Create: `mcp-server/tests/test_equity_detector.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for equity_detector tool."""

import pytest
from unittest.mock import MagicMock, patch
from healthpulse_mcp.tools.equity_detector import run


@pytest.fixture
def mock_domo():
    client = MagicMock()

    def side_effect(dataset_id, sql):
        if "hp_community" in dataset_id or "COMMUNITY" in str(sql):
            return [
                {"county_fips": "06037", "svi_score": "0.85", "uninsured_rate": "15.0", "poverty_rate": "20.0"},
                {"county_fips": "06001", "svi_score": "0.30", "uninsured_rate": "5.0", "poverty_rate": "8.0"},
            ]
        else:
            return [
                {"facility_id": "050001", "county_fips": "06037", "facility_name": "Vulnerable Hospital", "hospital_overall_rating": "2"},
                {"facility_id": "050002", "county_fips": "06001", "facility_name": "Affluent Hospital", "hospital_overall_rating": "4"},
            ]

    client.query_as_dicts.side_effect = side_effect
    return client


@pytest.mark.asyncio
async def test_flags_high_svi_facilities(mock_domo):
    with patch.dict("os.environ", {"HP_FACILITIES_DATASET_ID": "fac", "HP_COMMUNITY_DATASET_ID": "com", "HP_READMISSIONS_DATASET_ID": "rdm"}):
        result = await run(mock_domo, {"svi_threshold": 0.75, "outcome_measure": "readmission"})
    assert "equity_flags" in result
    assert len(result["equity_flags"]) >= 1


@pytest.mark.asyncio
async def test_includes_svi_score(mock_domo):
    with patch.dict("os.environ", {"HP_FACILITIES_DATASET_ID": "fac", "HP_COMMUNITY_DATASET_ID": "com", "HP_READMISSIONS_DATASET_ID": "rdm"}):
        result = await run(mock_domo, {"svi_threshold": 0.75})
    for flag in result["equity_flags"]:
        assert "svi_score" in flag
```

- [ ] **Step 2: Implement equity_detector.py**

```python
"""Equity Detector — Correlate facility outcomes with community social vulnerability."""

import os
from typing import Any

from healthpulse_mcp.domo_client import DomoClient


async def run(domo: DomoClient, args: dict[str, Any]) -> dict[str, Any]:
    """Detect equity disparities across facilities."""
    state = args.get("state")
    svi_threshold = args.get("svi_threshold", 0.75)
    outcome = args.get("outcome_measure", "readmission")

    # Get community health data (SVI scores by county)
    community_id = os.environ.get("HP_COMMUNITY_DATASET_ID", "")
    facilities_id = os.environ.get("HP_FACILITIES_DATASET_ID", "")

    if not community_id or not facilities_id:
        return {"error": "HP_COMMUNITY_DATASET_ID or HP_FACILITIES_DATASET_ID not configured"}

    # Fetch community data
    community_sql = f"SELECT county_fips, svi_score, uninsured_rate, poverty_rate FROM table WHERE svi_score <> 'Not Available'"
    community_data = domo.query_as_dicts(community_id, community_sql)
    svi_by_fips = {}
    for row in community_data:
        try:
            fips = row["county_fips"]
            svi_by_fips[fips] = {
                "svi_score": float(row["svi_score"]),
                "uninsured_rate": float(row.get("uninsured_rate", "0")),
                "poverty_rate": float(row.get("poverty_rate", "0")),
            }
        except (ValueError, TypeError):
            continue

    # Fetch facility data with county_fips
    fac_where = "county_fips <> ''"
    if state:
        fac_where += f" AND state = '{state}'"
    fac_sql = f"SELECT facility_id, facility_name, state, county_fips, hospital_overall_rating FROM table WHERE {fac_where}"
    facilities = domo.query_as_dicts(facilities_id, fac_sql)

    # Join and flag high-SVI facilities
    equity_flags = []
    for fac in facilities:
        fips = fac.get("county_fips")
        if not fips or fips not in svi_by_fips:
            continue
        svi = svi_by_fips[fips]
        if svi["svi_score"] >= svi_threshold:
            equity_flags.append({
                "facility_id": fac["facility_id"],
                "facility_name": fac["facility_name"],
                "state": fac.get("state", ""),
                "star_rating": fac.get("hospital_overall_rating", "N/A"),
                "county_fips": fips,
                "svi_score": svi["svi_score"],
                "uninsured_rate": svi["uninsured_rate"],
                "poverty_rate": svi["poverty_rate"],
            })

    # Sort by SVI score descending (most vulnerable first)
    equity_flags.sort(key=lambda x: x["svi_score"], reverse=True)

    # Compute disparity summary
    high_svi_ratings = [float(f["star_rating"]) for f in equity_flags if f["star_rating"] not in ("N/A", "Not Available")]
    low_svi_facs = [f for f in facilities if f.get("county_fips") in svi_by_fips and svi_by_fips[f["county_fips"]]["svi_score"] < svi_threshold]
    low_svi_ratings = [float(f.get("hospital_overall_rating", "0")) for f in low_svi_facs if f.get("hospital_overall_rating") not in ("N/A", "Not Available", "")]

    avg_high = sum(high_svi_ratings) / len(high_svi_ratings) if high_svi_ratings else 0
    avg_low = sum(low_svi_ratings) / len(low_svi_ratings) if low_svi_ratings else 0

    return {
        "equity_flags": equity_flags[:20],
        "total_high_svi_facilities": len(equity_flags),
        "disparity_summary": {
            "avg_star_rating_high_svi": round(avg_high, 2),
            "avg_star_rating_low_svi": round(avg_low, 2),
            "rating_gap": round(avg_low - avg_high, 2),
            "svi_threshold_used": svi_threshold,
        },
        "filters": {"state": state, "svi_threshold": svi_threshold, "outcome_measure": outcome},
    }
```

- [ ] **Step 3: Run tests**

Run: `cd mcp-server && pytest tests/test_equity_detector.py -v`
Expected: 2 tests PASS

- [ ] **Step 4: Commit**

```bash
git add mcp-server/src/healthpulse_mcp/tools/equity_detector.py mcp-server/tests/test_equity_detector.py
git commit -m "feat: add equity_detector MCP tool"
```

---

### Task 13: Facility Benchmark Tool

**Files:**
- Create: `mcp-server/src/healthpulse_mcp/tools/facility_benchmark.py`
- Create: `mcp-server/tests/test_facility_benchmark.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for facility_benchmark tool."""

import pytest
from unittest.mock import MagicMock, patch
from healthpulse_mcp.tools.facility_benchmark import run


@pytest.fixture
def mock_domo():
    client = MagicMock()
    client.query_as_dicts.return_value = [
        {"facility_id": "050001", "facility_name": "Hospital A", "hospital_overall_rating": "4", "state": "CA"},
        {"facility_id": "050002", "facility_name": "Hospital B", "hospital_overall_rating": "2", "state": "CA"},
    ]
    return client


@pytest.mark.asyncio
async def test_returns_comparison_for_two_facilities(mock_domo):
    with patch.dict("os.environ", {"HP_FACILITIES_DATASET_ID": "fac", "HP_QUALITY_DATASET_ID": "qual"}):
        result = await run(mock_domo, {"facility_ids": ["050001", "050002"]})
    assert "facilities" in result
    assert len(result["facilities"]) == 2


@pytest.mark.asyncio
async def test_includes_star_ratings(mock_domo):
    with patch.dict("os.environ", {"HP_FACILITIES_DATASET_ID": "fac", "HP_QUALITY_DATASET_ID": "qual"}):
        result = await run(mock_domo, {"facility_ids": ["050001", "050002"]})
    for fac in result["facilities"]:
        assert "hospital_overall_rating" in fac
```

- [ ] **Step 2: Implement facility_benchmark.py**

```python
"""Facility Benchmark — Compare facilities across quality dimensions."""

import os
from typing import Any

from healthpulse_mcp.domo_client import DomoClient


async def run(domo: DomoClient, args: dict[str, Any]) -> dict[str, Any]:
    """Compare facilities side-by-side."""
    facility_ids = args.get("facility_ids", [])
    if len(facility_ids) < 2:
        return {"error": "At least 2 facility_ids required"}

    id_list = ", ".join(f"'{fid}'" for fid in facility_ids)

    # Fetch facility profiles
    fac_id = os.environ.get("HP_FACILITIES_DATASET_ID", "")
    facilities = []
    if fac_id:
        sql = f"SELECT facility_id, facility_name, state, hospital_type, hospital_overall_rating FROM table WHERE facility_id IN ({id_list})"
        facilities = domo.query_as_dicts(fac_id, sql)

    # Fetch quality measures for these facilities
    qual_id = os.environ.get("HP_QUALITY_DATASET_ID", "")
    quality = []
    if qual_id:
        sql = f"SELECT facility_id, measure_id, measure_name, score, compared_to_national FROM table WHERE facility_id IN ({id_list})"
        quality = domo.query_as_dicts(qual_id, sql)

    # Fetch readmission data
    readm_id = os.environ.get("HP_READMISSIONS_DATASET_ID", "")
    readmissions = []
    if readm_id:
        sql = f"SELECT facility_id, measure_name, excess_readmission_ratio FROM table WHERE facility_id IN ({id_list})"
        readmissions = domo.query_as_dicts(readm_id, sql)

    # Organize by facility
    by_facility = {}
    for fac in facilities:
        fid = fac["facility_id"]
        by_facility[fid] = {
            **fac,
            "quality_measures": [q for q in quality if q["facility_id"] == fid],
            "readmissions": [r for r in readmissions if r["facility_id"] == fid],
        }

    return {
        "facilities": list(by_facility.values()),
        "comparison_count": len(by_facility),
    }
```

- [ ] **Step 3: Run tests**

Run: `cd mcp-server && pytest tests/test_facility_benchmark.py -v`
Expected: 2 tests PASS

- [ ] **Step 4: Commit**

```bash
git add mcp-server/src/healthpulse_mcp/tools/facility_benchmark.py mcp-server/tests/test_facility_benchmark.py
git commit -m "feat: add facility_benchmark MCP tool"
```

---

### Task 14: Executive Briefing Tool

**Files:**
- Create: `mcp-server/src/healthpulse_mcp/tools/executive_briefing.py`
- Create: `mcp-server/tests/test_executive_briefing.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for executive_briefing tool."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from healthpulse_mcp.tools.executive_briefing import run


@pytest.fixture
def mock_domo():
    client = MagicMock()
    client.query_as_dicts.return_value = [
        {"facility_id": "050001", "facility_name": "Hospital A", "hospital_overall_rating": "4", "state": "CA"},
        {"facility_id": "050002", "facility_name": "Hospital B", "hospital_overall_rating": "1", "state": "CA"},
    ]
    return client


@pytest.mark.asyncio
async def test_returns_structured_briefing(mock_domo):
    with patch.dict("os.environ", {"HP_FACILITIES_DATASET_ID": "fac", "HP_QUALITY_DATASET_ID": "qual", "HP_READMISSIONS_DATASET_ID": "rdm"}):
        result = await run(mock_domo, {"scope": "state", "state": "CA"})
    assert "summary_stats" in result
    assert "suggested_prompt" in result


@pytest.mark.asyncio
async def test_briefing_includes_suggested_prompt(mock_domo):
    with patch.dict("os.environ", {"HP_FACILITIES_DATASET_ID": "fac", "HP_QUALITY_DATASET_ID": "qual", "HP_READMISSIONS_DATASET_ID": "rdm"}):
        result = await run(mock_domo, {"scope": "state", "state": "CA"})
    assert "healthcare quality analyst" in result["suggested_prompt"].lower()


@pytest.mark.asyncio
async def test_briefing_does_not_call_llm(mock_domo):
    """Executive briefing must NOT call any LLM — returns data only."""
    with patch.dict("os.environ", {"HP_FACILITIES_DATASET_ID": "fac", "HP_QUALITY_DATASET_ID": "qual", "HP_READMISSIONS_DATASET_ID": "rdm"}):
        result = await run(mock_domo, {"scope": "state", "state": "CA"})
    # No 'executive_summary' key (that would indicate LLM generation)
    assert "executive_summary" not in result or result.get("executive_summary") is None
```

- [ ] **Step 2: Implement executive_briefing.py**

```python
"""Executive Briefing — Aggregate analytics for narrative generation.

Returns structured data. Does NOT call any LLM.
The calling agent (Prompt Opinion platform or dashboard) generates the narrative.
"""

import os
from typing import Any

from healthpulse_mcp.analytics import detect_anomalies
from healthpulse_mcp.domo_client import DomoClient

SUGGESTED_PROMPT = """You are a healthcare quality analyst preparing an executive briefing for hospital leadership.

Based on the structured data below, generate a narrative briefing with:
1. Executive summary (2-3 sentences)
2. Key findings (3-5 bullet points)
3. Anomalies requiring attention (with specific facility names and measures)
4. Equity insights (if included)
5. Recommended actions (prioritized)

Focus on actionable insights. Use specific numbers. Flag anything that requires immediate attention."""


async def run(domo: DomoClient, args: dict[str, Any]) -> dict[str, Any]:
    """Aggregate analytics into structured briefing data."""
    scope = args.get("scope", "state")
    state = args.get("state")
    facility_ids = args.get("facility_ids", [])
    include_equity = args.get("include_equity", True)

    fac_id = os.environ.get("HP_FACILITIES_DATASET_ID", "")
    qual_id = os.environ.get("HP_QUALITY_DATASET_ID", "")
    readm_id = os.environ.get("HP_READMISSIONS_DATASET_ID", "")

    # Build state/facility filter
    where = "1=1"
    if scope == "state" and state:
        where = f"state = '{state}'"
    elif scope == "facility" and facility_ids:
        id_list = ", ".join(f"'{fid}'" for fid in facility_ids)
        where = f"facility_id IN ({id_list})"

    # Fetch facility summary
    facilities = []
    if fac_id:
        sql = f"SELECT facility_id, facility_name, state, hospital_overall_rating FROM table WHERE {where}"
        facilities = domo.query_as_dicts(fac_id, sql)

    ratings = [float(f["hospital_overall_rating"]) for f in facilities
               if f.get("hospital_overall_rating") not in ("Not Available", "", None)]

    # Fetch quality data for anomaly detection
    quality_data = []
    if qual_id:
        sql = f"SELECT facility_id, measure_id, measure_name, score, compared_to_national FROM table WHERE {where.replace('state', 'state')}"
        quality_data = domo.query_as_dicts(qual_id, sql)

    anomalies = detect_anomalies(quality_data, score_key="score", threshold=2.0)

    # Fetch readmission gaps
    care_gaps = []
    if readm_id:
        sql = f"SELECT facility_id, facility_name, measure_name, excess_readmission_ratio FROM table WHERE excess_readmission_ratio <> 'Not Available'"
        readm_data = domo.query_as_dicts(readm_id, sql)
        care_gaps = [r for r in readm_data
                     if float(r.get("excess_readmission_ratio", "0")) > 1.05]

    # Build top/bottom performers
    rated_facilities = sorted(
        [f for f in facilities if f.get("hospital_overall_rating") not in ("Not Available", "")],
        key=lambda f: float(f.get("hospital_overall_rating", "0")),
        reverse=True,
    )

    return {
        "summary_stats": {
            "total_facilities": len(facilities),
            "anomaly_count": len(anomalies),
            "care_gap_count": len(care_gaps),
            "avg_star_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
        },
        "anomalies": anomalies[:10],
        "care_gaps": care_gaps[:10],
        "top_performers": rated_facilities[:5],
        "bottom_performers": rated_facilities[-5:] if len(rated_facilities) > 5 else [],
        "suggested_prompt": SUGGESTED_PROMPT,
        "filters": {"scope": scope, "state": state, "include_equity": include_equity},
    }
```

- [ ] **Step 3: Run tests**

Run: `cd mcp-server && pytest tests/test_executive_briefing.py -v`
Expected: 3 tests PASS

- [ ] **Step 4: Commit**

```bash
git add mcp-server/src/healthpulse_mcp/tools/executive_briefing.py mcp-server/tests/test_executive_briefing.py
git commit -m "feat: add executive_briefing MCP tool (data-only, no LLM)"
```

---

### Task 15: MCP Server conftest + Full Integration Test

**Files:**
- Create: `mcp-server/tests/conftest.py`
- Create: `mcp-server/tests/test_integration.py`

- [ ] **Step 1: Create conftest.py with shared fixtures**

```python
"""Shared test fixtures for HealthPulse MCP tests."""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_domo_client():
    """Create a mock Domo client with configurable responses."""
    client = MagicMock()
    client.query_as_dicts.return_value = []
    client.query.return_value = {"columns": [], "rows": [], "numRows": 0}
    return client
```

- [ ] **Step 2: Create integration test**

```python
"""Integration test — verify all tools are callable through the server."""

import pytest
from healthpulse_mcp.server import list_tools


@pytest.mark.asyncio
async def test_all_tools_registered():
    tools = await list_tools()
    names = {t.name for t in tools}
    expected = {"quality_monitor", "care_gap_finder", "equity_detector",
                "facility_benchmark", "executive_briefing"}
    assert names == expected


@pytest.mark.asyncio
async def test_all_tools_have_descriptions():
    tools = await list_tools()
    for tool in tools:
        assert len(tool.description) > 20, f"{tool.name} needs a better description"


@pytest.mark.asyncio
async def test_all_tools_have_valid_schemas():
    tools = await list_tools()
    for tool in tools:
        schema = tool.inputSchema
        assert schema["type"] == "object"
        assert "properties" in schema
```

- [ ] **Step 3: Run full test suite**

Run: `cd mcp-server && pytest -v`
Expected: All tests PASS (25+ tests)

- [ ] **Step 4: Commit**

```bash
git add mcp-server/tests/conftest.py mcp-server/tests/test_integration.py
git commit -m "test: add conftest fixtures and integration tests"
```

---

## Chunk 4: Dashboard + Polish + Submission (High-Level)

> Tasks 16-22 are higher-level because they depend on the MCP server being complete and the Prompt Opinion platform being explored. Detailed bite-sized steps will be expanded when these tasks are started.

### Task 16: Prompt Opinion Platform Exploration & Hello World

- [ ] Register at https://app.promptopinion.ai
- [ ] Watch getting-started video: https://youtu.be/Qvs_QK4meHc
- [ ] Clone and study reference repos: `po-community-mcp`, `po-adk-python`
- [ ] Deploy hello-world MCP server to marketplace
- [ ] Verify it's discoverable and invokable
- [ ] Document the publishing flow in `docs/prompt-opinion-guide.md`

**Gate:** Can publish and invoke a minimal MCP server on Prompt Opinion.

### Task 17: Publish HealthPulse MCP Server to Prompt Opinion

- [ ] Configure HealthPulse MCP server for Prompt Opinion deployment
- [ ] Publish to marketplace with all 5 tools
- [ ] Test each tool invocation through the platform
- [ ] Verify SHARP capability advertisement works
- [ ] Document any platform-specific adaptations needed

**Gate:** All 5 tools invokable through Prompt Opinion platform.

### Task 18: Next.js Dashboard Setup

- [ ] Initialize Next.js 16 project in `web/`
- [ ] Install dependencies (Tailwind v4, Recharts, @react-pdf/renderer, Anthropic SDK)
- [ ] Cherry-pick DomoClient, KPIEngine, BriefingGenerator from inspection-intelligence
- [ ] Create types/index.ts with HealthPulse interfaces
- [ ] Build landing page
- [ ] Write initial tests

**Gate:** Dashboard builds and serves locally.

### Task 19: Dashboard Pages

- [ ] Dashboard page (6 KPI cards + anomaly alerts)
- [ ] Facilities page (sortable table with quality scores)
- [ ] Compare page (side-by-side facility comparison + AI narrative)
- [ ] Equity page (SVI disparity analysis)
- [ ] Briefing page (executive briefing + PDF export)
- [ ] Write tests for each page component

**Gate:** All 5 pages working with real CMS data.

### Task 20: FHIR Layer (Phase 2)

- [ ] Deploy HAPI FHIR via Docker (`docker run -p 8080:8080 hapiproject/hapi:latest`)
- [ ] Download pre-built Synthea dataset from synthea.mitre.org/downloads
- [ ] Load patients into FHIR server
- [ ] Add FHIR-aware tools to MCP server (patient lookup when SHARP headers present)
- [ ] Update Prompt Opinion Marketplace publishing
- [ ] Test patient drill-down in Prompt Opinion

**Gate:** Agent can answer "show me high-risk patients at facility X" when FHIR context provided.

### Task 21: Demo Video + Submission Assets

- [ ] Write demo script (3 minutes, inside Prompt Opinion platform)
- [ ] Record demo video showing: quality anomaly detection, facility benchmark, equity analysis, executive briefing
- [ ] Upload to YouTube (publicly available)
- [ ] Create architecture diagram (Domo MCP + SHARP + FHIR + Prompt Opinion)
- [ ] Take screenshots of agent working in Prompt Opinion
- [ ] Write submission text addressing AI Factor, Healthcare Impact, Feasibility
- [ ] Polish README with setup instructions

**Gate:** All submission assets ready.

### Task 22: Final Submission

- [ ] Run full test suite (target: 200+)
- [ ] Verify Stage 1 qualification checklist (spec Section 0)
- [ ] Submit on Devpost with: description, marketplace URL, video URL, code repo
- [ ] Verify submission is visible on Devpost

**Gate:** Submission complete. All Section 0 checklist items checked.
