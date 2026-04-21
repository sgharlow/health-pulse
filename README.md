# HealthPulse AI

![Tests](https://github.com/sgharlow/health-pulse/actions/workflows/test.yml/badge.svg)

> Healthcare Performance Intelligence MCP Server + Dashboard

## For Judges — Agents Assemble Hackathon

| | |
|---|---|
| **Live Dashboard** | https://web-umber-alpha-41.vercel.app |
| **Live MCP Server** | https://health-pulse-mcp-production.up.railway.app/mcp |
| **Submission Brief** | [`SUBMISSION.md`](./SUBMISSION.md) (root) → [`assets/SUBMISSION.md`](./assets/SUBMISSION.md) (detailed) |
| **Demo Script** | [`assets/VIDEO-SCRIPT.md`](./assets/VIDEO-SCRIPT.md) |
| **Demo Screenshots** | [`assets/screenshots/`](./assets/screenshots/) (10 numbered PNGs) |
| **Architecture** | [`assets/architecture.md`](./assets/architecture.md) |
| **License** | MIT (see [`LICENSE`](./LICENSE)) |
| **Author** | Steve Harlow ([github.com/sgharlow](https://github.com/sgharlow)) |
| **Demo Video** | https://youtu.be/40haMLuDOIk |

**One-line summary:** 11-tool MCP server + Next.js dashboard surfacing 233K+ rows of real CMS hospital data (5,400+ facilities), backed by 313 automated tests and deployed to production.

---


HealthPulse AI is a Model Context Protocol (MCP) server and Next.js dashboard that surfaces actionable intelligence from 233,000+ rows of real CMS hospital quality data across 5,400+ US facilities and 100 synthetic FHIR patients. It gives AI agents eleven analytics tools spanning quality anomaly detection, care gap identification, health equity analysis, facility benchmarking, executive briefing generation, state-level ranking, cross-cutting multi-factor risk analysis, patient-level risk profiling, cohort analysis, patient experience scoring, and cost efficiency analysis — all backed by real public data loaded into Domo, synthetic FHIR patient data from Synthea, and served over a production HTTPS endpoint with a conversational chat interface and AI narrative briefing.

## What It Does

HealthPulse AI provides 11 MCP tools spanning quality monitoring, care gap identification, health equity analysis, facility benchmarking, executive briefing generation, state-level ranking, cross-cutting multi-factor risk analysis, patient-level risk profiling, cohort analysis, patient experience scoring, and cost efficiency analysis.

## Architecture

The system consists of a Python MCP server, a Next.js dashboard, and a conversational chat interface. The MCP server connects to Domo for CMS data and includes a synthetic FHIR patient layer for patient-level analysis demonstrations.

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

HealthPulse AI includes a synthetic patient data layer powered by Synthea FHIR bundles, demonstrating how population-level analytics can bridge to individual patient-level analysis when connected to a FHIR-enabled EHR.

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
#   DOMO_CLIENT_ID           (get from https://developer.domo.com/)
#   DOMO_CLIENT_SECRET       (get from https://developer.domo.com/)
#   DOMO_INSTANCE            (your-subdomain.domo.com)
#   HP_FACILITIES_DATASET_ID
#   HP_QUALITY_DATASET_ID
#   HP_READMISSIONS_DATASET_ID
#   HP_COMMUNITY_DATASET_ID
#   HP_EXPERIENCE_DATASET_ID
#   HP_SAFETY_DATASET_ID     (used by cross_cutting_analysis tool)
#   HP_COST_DATASET_ID       (used by cost_efficiency tool)
#   HP_API_KEY               (optional — enables auth middleware)

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
# MCP server tests (250 tests)
cd mcp-server
pytest

# Web dashboard tests (63 tests)
cd web
npm test
```

## MCP Tools

The server exposes 11 tools: `quality_monitor`, `care_gap_finder`, `equity_detector`, `facility_benchmark`, `executive_briefing`, `state_ranking`, `cross_cutting_analysis`, `patient_risk_profile`, `patient_cohort_analysis`, `patient_experience`, and `cost_efficiency`. See the MCP server documentation for tool parameters and output schemas.

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
| Analytics | Statistical anomaly detection and multi-dimensional analysis |
| Healthcare Context | FHIR-aware context propagation |
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
