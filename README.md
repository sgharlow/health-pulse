# HealthPulse AI

![Tests](https://github.com/sgharlow/health-pulse/actions/workflows/test.yml/badge.svg)

> Healthcare Performance Intelligence MCP Server + Dashboard

HealthPulse AI is a Model Context Protocol (MCP) server and Next.js dashboard that surfaces actionable intelligence from 233,000+ rows of real CMS hospital quality data across 5,400+ US facilities and 100 synthetic FHIR patients. It gives AI agents eleven analytics tools spanning quality anomaly detection, care gap identification, health equity analysis, facility benchmarking, executive briefing generation, state-level ranking, cross-cutting multi-factor risk analysis, patient-level risk profiling, cohort analysis, patient experience scoring, and cost efficiency analysis — all backed by real public data loaded into Domo, synthetic FHIR patient data from Synthea, and served over a production HTTPS endpoint with a conversational chat interface and AI narrative briefing.

## What It Does

- **quality_monitor** — Detects statistical anomalies in CMS hospital quality measures (mortality, readmission, safety, timeliness) using Z-score analysis across all facilities or filtered by state; returns the top 20 anomalous facilities ranked by severity.
- **care_gap_finder** — Identifies facilities with excess readmission ratios above threshold or quality measures rated worse than the national rate; returns up to 30 facilities sorted by excess ratio.
- **equity_detector** — Correlates facility outcomes with county-level CDC Social Vulnerability Index (SVI) scores to flag facilities in high-vulnerability areas and compute star-rating disparity between high- and low-SVI populations.
- **facility_benchmark** — Benchmarks specific hospitals against each other across quality measures and readmission rates given a list of CMS facility IDs.
- **executive_briefing** — Aggregates quality anomalies, readmission gaps, and equity indicators into a structured data package with a `suggested_prompt` field ready for LLM narrative generation (the server itself never calls an LLM).
- **state_ranking** — Ranks all US states by composite healthcare performance score combining star ratings, worse-than-national rates, and facility counts.
- **cross_cutting_analysis** — Finds facilities with multiple simultaneous concerns across 6 dimensions: quality, readmissions, equity, patient experience, cost efficiency, and star ratings. Identifies compounding risk factors invisible in siloed analysis.
- **patient_risk_profile** — Generates a comprehensive risk profile for a synthetic FHIR patient including active conditions, medications, recent encounters, and risk factors derived from clinical data.
- **patient_cohort_analysis** — Analyzes cohorts of synthetic patients by condition, age group, or risk level to identify population health trends and intervention opportunities.
- **patient_experience** — Analyzes HCAHPS patient survey data to surface how patients rate their hospital care across communication, responsiveness, environment, and discharge planning dimensions.
- **cost_efficiency** — Correlates Medicare spending per beneficiary with quality outcomes to identify facilities delivering high-quality care at lower cost and those with spending-quality misalignment.

## Key Findings from Real Data

These are not synthetic examples. HealthPulse AI discovered these patterns from 233,000+ rows of real CMS hospital quality data:

- **450 quality measures** rated worse than national benchmarks across 5,426 US hospitals, with California, New York, and Florida carrying the highest concentration of low-rated facilities.

- **0.77-star rating disparity** between hospitals in high-vulnerability communities (SVI >= 0.75, avg 2.75 stars) and low-vulnerability communities (SVI < 0.25, avg 3.53 stars) — a systemic equity gap affecting 1,708 facilities serving vulnerable populations.

- **48% excess hip/knee readmissions** at UCI Health - Los Alamitos, 43% excess at Providence St. Mary Medical Center and Oroville Hospital — specific, actionable care gaps identified by the care_gap_finder tool.

- **52.2% of overspending California hospitals** also have below-average star ratings, suggesting that higher Medicare spending does not correlate with better quality outcomes.

- **94 of 222 Florida hospitals (42%)** have two or more simultaneous concerns spanning quality, readmissions, equity, and star ratings — compounding risk factors invisible in any single-dimension analysis.

Every number above came from a single MCP tool call against real, public CMS data.

## Architecture

```
Access Points
  1. Prompt Opinion Marketplace (MCP tool invocation)
  2. Next.js Dashboard (visual analytics + AI briefing + PDF export)
  3. Chat Interface (conversational tool routing via Claude)
        |
        | MCP (Streamable HTTP) / REST API / Claude SDK
        v
HealthPulse AI MCP Server  [Railway / Docker]
  - ApiKeyMiddleware
  - SharpMiddleware (SHARP/FHIR context)
  - 11 FastMCP tools
  - 6 MCP resources (4 static + 2 URI templates)
        |
        |----- Domo REST API (OAuth) -----> Domo Platform
        |                                    7 CMS datasets (233K+ rows)
        |
        |----- FHIR/Synthea Data ---------> Synthetic Patient Layer
                                             100 patients, 1,002 resources

Data Sources
  - CMS Hospital Quality Data (public, de-identified)
  - CDC Social Vulnerability Index
  - Synthea FHIR Synthetic Patients
```

SHARP headers (`X-FHIR-Server-URL`, `X-Patient-ID`, `X-FHIR-Access-Token`) are extracted per-request and made available to tools via a context variable, enabling FHIR-aware patient-level analysis with synthetic data today and real EHR integration in production.

## Data Sources

| Dataset | Rows (approx.) | What It Measures |
|---------|---------------|-----------------|
| CMS Hospital General Information | 5,400+ | Facility metadata, state, county FIPS, star rating, hospital type |
| CMS Hospital Quality Measures | ~160,000 | Per-facility measure scores (mortality, readmission, safety, timeliness) |
| CMS Readmission & Death Measures | ~30,000 | Excess readmission ratios, national comparison |
| CMS Patient Survey (HCAHPS) | ~25,000 | Patient experience scores |
| CMS Timely & Effective Care | ~10,000 | Operational performance measures |
| CMS Complications & Deaths | ~5,000 | Complication rates and death measures |
| CDC Social Vulnerability Index | ~3,200 | County-level SVI percentile scores |
| Synthea FHIR Synthetic Patients | 1,002 resources | 100 patients with conditions, medications, encounters, observations |

**Total: 233,000+ rows across 7 Domo datasets + 100 synthetic FHIR patients (1,002 resources)**

All CMS/CDC data is publicly available. Synthea data is fully synthetic. No Protected Health Information (PHI) is stored or processed.

## Dashboard

The Next.js dashboard provides 7 pages of visual analytics, conversational AI, and export capabilities:

| Page | What It Shows |
|------|--------------|
| **Hub** (`/`) | Unified entry point linking Dashboard, Chat, and Prompt Opinion Marketplace |
| **Dashboard** (`/dashboard`) | KPI cards, star distribution charts, quality flags across all states |
| **Facilities** (`/facilities`) | Searchable, sortable facility table with ratings and detail drill-down |
| **Compare** (`/compare`) | Side-by-side facility benchmarking with quality measure comparison |
| **Equity** (`/equity`) | SVI-correlated outcomes, star-rating disparity between high/low-SVI communities |
| **Briefing** (`/briefing`) | AI-generated narrative briefings with PDF export via @react-pdf/renderer |
| **Chat** (`/chat`) | Conversational access to all 11 MCP tools via Claude with tool routing |

The chat interface uses the Anthropic SDK (`@anthropic-ai/sdk`) to route natural language questions to the appropriate MCP tool, returning structured results with AI-generated context.

The executive briefing page generates narrative summaries from structured tool output and supports PDF export for offline sharing.

## FHIR/Synthea Integration

HealthPulse AI includes a synthetic patient data layer powered by Synthea FHIR bundles:

- **100 synthetic patients** with realistic clinical histories (conditions, medications, encounters, observations)
- **1,002 FHIR resources** loaded and indexed for patient-level analysis
- **SHARP headers** propagate FHIR context (server URL, patient ID, access token) through every MCP request
- **patient_risk_profile** tool generates comprehensive risk assessments from individual patient FHIR data
- **patient_cohort_analysis** tool analyzes patient populations by condition, demographics, or risk level

This demonstrates how the same MCP tools that analyze population-level CMS data can drill down to individual patients when connected to a FHIR-enabled EHR — bridging the gap between facility analytics and clinical decision support.

## Quick Start

### Prerequisites

- Python 3.11+
- A Domo account with API credentials (client ID and client secret)
- CMS datasets loaded into Domo (see `scripts/load_cms_data.py`)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/sgharlow/health-pulse
cd health-pulse

# 2. Install the MCP server
cd mcp-server
pip install -e ".[dev]"

# 3. Configure environment variables
cp ../.env.example .env
# Edit .env and fill in:
#   DOMO_CLIENT_ID
#   DOMO_CLIENT_SECRET
#   HP_FACILITIES_DATASET_ID
#   HP_QUALITY_DATASET_ID
#   HP_READMISSIONS_DATASET_ID
#   HP_COMMUNITY_DATASET_ID
#   HP_EXPERIENCE_DATASET_ID
#   HP_API_KEY  (optional — enables auth)

# 4. Load CMS data into Domo (one-time)
cd ../scripts
pip install -r requirements.txt
python load_cms_data.py

# 5. Run the MCP server
cd ../mcp-server
python -m healthpulse_mcp.server
# Server listens on http://0.0.0.0:8000/mcp

# 6. Run the dashboard (optional)
cd ../web
npm install
npm run dev
# Dashboard at http://localhost:3000
```

### Running Tests

```bash
# MCP server tests (243 tests)
cd mcp-server
pytest

# Web dashboard tests (63 tests)
cd web
npm test
```

## MCP Tools Reference

### `quality_monitor`

Detect statistical anomalies in CMS hospital quality measures.

**Inputs:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `measure_group` | string | `"all"` | One of: `mortality`, `readmission`, `safety`, `timeliness`, `all` |
| `state` | string | `null` | Two-letter US state code (e.g. `"CA"`) |
| `threshold_sigma` | float | `2.0` | Z-score threshold for flagging anomalies |

**Output:** `{ total_facilities_analyzed, measures_checked, anomaly_count, anomalies[], filters }`

Each anomaly includes `facility_id`, `measure_id`, `score`, `z_score`, `severity` (`critical` / `high` / `medium`).

---

### `care_gap_finder`

Identify facilities with excess readmissions or below-national-rate quality scores.

**Inputs:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gap_type` | string | `"all"` | One of: `readmission`, `mortality`, `safety`, `all` |
| `state` | string | `null` | Two-letter US state code |
| `min_excess_ratio` | float | `1.05` | Minimum excess readmission ratio to flag |

**Output:** `{ gaps[], total_gaps, filters }`

---

### `equity_detector`

Detect health equity gaps using CDC Social Vulnerability Index data.

**Inputs:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `outcome_measure` | string | `"readmission"` | One of: `readmission`, `mortality`, `safety` |
| `state` | string | `null` | Two-letter US state code |
| `svi_threshold` | float | `0.75` | SVI percentile cutoff for high-vulnerability classification |

**Output:** `{ equity_flags[], disparity_summary, filters }`

`disparity_summary` includes average star ratings for high-SVI vs low-SVI facilities and the computed rating gap.

---

### `facility_benchmark`

Benchmark specific hospitals against each other.

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `facility_ids` | list[string] | Yes | CMS facility IDs (e.g. `["100001", "100002"]`) |
| `measures` | list[string] | No | Specific measure IDs to include (e.g. `["MORT_30_AMI"]`) |

**Output:** `{ facilities[], benchmarks[], filters }`

---

### `executive_briefing`

Generate a structured briefing aggregating quality, readmissions, and equity data.

**Inputs:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `scope` | string | `"network"` | One of: `state`, `facility`, `network` |
| `state` | string | `null` | Required when `scope="state"` |
| `facility_ids` | list[string] | `[]` | Used when `scope="facility"` |
| `include_equity` | bool | `true` | Include SVI-based equity analysis |

**Output:** `{ summary, quality_anomalies[], care_gaps[], equity_summary, suggested_prompt }`

The `suggested_prompt` field contains a ready-to-use prompt string for generating an executive narrative from the structured data.

---

### `state_ranking`

Ranks all US states by composite healthcare performance score.

**Input:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 10 | Number of states to return |
| `order` | string | "worst" | Sort order: "worst" or "best" first |

**Output:** Rankings with state, facility_count, avg_star_rating, worse_than_national_pct, composite_score (0-100).

---

### `cross_cutting_analysis`

Finds facilities with MULTIPLE simultaneous concerns across quality, readmissions, equity, and star ratings. This is the AI differentiator — identifies compounding risk factors invisible in siloed analysis.

**Input:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `state` | string | (all) | Optional 2-letter state code |

**Output:** Multi-concern facilities with concern_count, list of concerns, SVI data, systemic patterns detected.

---

### `patient_risk_profile`

Generate a risk profile for a facility's patients or a specific synthetic FHIR patient.

**Input:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `facility_id` | string | Yes | CMS facility CCN ID (e.g. `"050454"`) |
| `patient_id` | string | No | Specific Synthea patient UUID; if omitted, returns facility-level risk summary. Also sourced from SHARP `X-Patient-ID` header. |

**Output:** Single patient: `{ patient, conditions[], observations[], risk_factors[], readmission_risk }`. Facility: `{ total_patients, risk_distribution, high_risk_patients[] }`.

---

### `patient_cohort_analysis`

Analyze cohorts of synthetic patients at a facility by condition or risk level.

**Input:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `facility_id` | string | Yes | CMS facility CCN ID (e.g. `"050454"`) |
| `condition` | string | No | Filter by CMS condition group (e.g. `"heart-failure"`, `"diabetes"`, `"copd"`) |
| `risk_level` | string | No | Filter by risk level: `high`, `medium`, `low` |

**Output:** `{ cohort, filters, readmission_indicators, cms_context, clinical_context }`

---

### `patient_experience`

Analyze HCAHPS patient survey data to surface how patients rate their hospital care.

**Input:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `state` | string | `null` | Two-letter US state code |
| `measure` | string | `"all"` | Category: `communication`, `responsiveness`, `environment`, `overall`, `all` |
| `min_star_rating` | float | `null` | Filter to facilities below this rating (find worst performers) |
| `limit` | int | `20` | Max facilities to return |

**Output:** `{ total_facilities_analyzed, summary, worst_facilities[], category_averages, clinical_context, filters }`

---

### `cost_efficiency`

Analyze Medicare spending per beneficiary and correlate with quality outcomes.

**Input:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `state` | string | `null` | Two-letter US state code |
| `spending_threshold` | float | `1.1` | Ratio above which a facility is flagged as overspending (1.0 = national avg) |
| `limit` | int | `20` | Max overspenders to return |

**Output:** `{ total_facilities_analyzed, summary, overspenders[], cost_quality_correlation, clinical_context, filters }`

## Deployment

The system has two deployment targets:

**MCP Server (Railway):** `https://health-pulse-mcp-production.up.railway.app/mcp`

The MCP server is deployed as a Docker container on Railway. Railway auto-detects the Dockerfile and deploys on push. Environment variables are configured in Railway's dashboard.

```bash
# Build locally
docker build -t healthpulse-mcp .
docker run -p 8000:8000 --env-file mcp-server/.env healthpulse-mcp
```

**Dashboard (Vercel):** `https://web-umber-alpha-41.vercel.app`

The Next.js dashboard is deployed on Vercel with automatic deployments from the `web/` directory. It connects to the Railway MCP server for data and uses the Anthropic SDK for the chat interface.

## Hackathon

- **Hackathon:** Agents Assemble — Healthcare AI
- **Platform:** Prompt Opinion
- **Prize Pool:** $25,000
- **Deadline:** May 11
- **Submission:** `assets/SUBMISSION.md`

## Tech Stack

| Layer | Technology |
|-------|-----------|
| MCP Framework | FastMCP (Python MCP SDK) |
| Transport | Streamable HTTP, stateless mode |
| Web Server | Uvicorn + Starlette |
| Language (Server) | Python 3.11 |
| Language (Dashboard) | TypeScript |
| Data Platform | Domo (REST API + SQL query endpoint) |
| Data Source | CMS Hospital Quality Data (public), CDC SVI, Synthea FHIR |
| Analytics | Z-score anomaly detection, cross-cutting risk analysis, cohort analysis |
| Healthcare Context | SHARP-on-MCP (X-FHIR-* headers) |
| Dashboard | Next.js 16, TypeScript, Tailwind CSS, Recharts |
| AI Chat | @anthropic-ai/sdk (Claude tool routing) |
| PDF Export | @react-pdf/renderer |
| Testing (Server) | pytest, pytest-asyncio (250 tests) |
| Testing (Dashboard) | Vitest (63 tests) |
| Deployment (MCP) | Docker on Railway |
| Deployment (Dashboard) | Vercel |
| Auth | Optional API key middleware |

**Total: 313 tests (250 MCP server + 63 web dashboard)**

## License

MIT
