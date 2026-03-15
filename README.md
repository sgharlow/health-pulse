# HealthPulse AI

> Healthcare Performance Intelligence MCP Server

HealthPulse AI is a Model Context Protocol (MCP) server that surfaces actionable intelligence from 233,000+ rows of real CMS hospital quality data across 5,400+ US facilities. It gives AI agents five analytics tools covering quality anomaly detection, care gap identification, health equity analysis, facility benchmarking, and executive briefing generation — all backed by real public data loaded into Domo and served over a production HTTPS endpoint.

## What It Does

- **quality_monitor** — Detects statistical anomalies in CMS hospital quality measures (mortality, readmission, safety, timeliness) using Z-score analysis across all facilities or filtered by state; returns the top 20 anomalous facilities ranked by severity.
- **care_gap_finder** — Identifies facilities with excess readmission ratios above threshold or quality measures rated worse than the national rate; returns up to 30 facilities sorted by excess ratio.
- **equity_detector** — Correlates facility outcomes with county-level CDC Social Vulnerability Index (SVI) scores to flag facilities in high-vulnerability areas and compute star-rating disparity between high- and low-SVI populations.
- **facility_benchmark** — Benchmarks specific hospitals against each other across quality measures and readmission rates given a list of CMS facility IDs.
- **executive_briefing** — Aggregates quality anomalies, readmission gaps, and equity indicators into a structured data package with a `suggested_prompt` field ready for LLM narrative generation (the server itself never calls an LLM).

## Architecture

```
Prompt Opinion Marketplace
        |
        | MCP (Streamable HTTP)
        v
HealthPulse AI MCP Server  [Railway / Docker]
  - ApiKeyMiddleware
  - SharpMiddleware (SHARP/FHIR context)
  - 5 FastMCP tools
        |
        | Domo REST API (OAuth)
        v
Domo Platform
  - 7 CMS datasets (233K+ rows)
        |
        | Source
        v
CMS Hospital Quality Data (public, de-identified)
```

SHARP headers (`X-FHIR-Server-URL`, `X-Patient-ID`, `X-FHIR-Access-Token`) are extracted per-request and made available to tools via a context variable, enabling future FHIR-aware personalisation without requiring PHI.

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

**Total: 233,000+ rows across 7 Domo datasets**

All data is publicly available CMS/CDC data. No Protected Health Information (PHI) is stored or processed.

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
```

### Running Tests

```bash
cd mcp-server
pytest
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

## Deployment

The server is deployed as a Docker container on Railway.

**Production endpoint:** `https://health-pulse-mcp-production.up.railway.app/mcp`

```bash
# Build locally
docker build -t healthpulse-mcp .
docker run -p 8000:8000 --env-file mcp-server/.env healthpulse-mcp
```

The `Dockerfile` at the project root copies the `mcp-server/` package and runs `python -m healthpulse_mcp.server`. Railway auto-detects the Dockerfile and deploys on push.

Environment variables are configured in Railway's dashboard. The server picks up `PORT` from the environment automatically.

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
| Language | Python 3.11 |
| Data Platform | Domo (REST API + SQL query endpoint) |
| Data Source | CMS Hospital Quality Data (public), CDC SVI |
| Analytics | Z-score anomaly detection (custom implementation) |
| Healthcare Context | SHARP-on-MCP (X-FHIR-* headers) |
| Dashboard | Next.js 16, TypeScript, Tailwind CSS |
| Testing | pytest, pytest-asyncio (80+ unit tests) |
| Deployment | Docker on Railway |
| Auth | Optional API key middleware |

## License

MIT
