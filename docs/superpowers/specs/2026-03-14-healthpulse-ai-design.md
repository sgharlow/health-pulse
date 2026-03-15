# HealthPulse AI — Design Specification

> **Project:** Agents Assemble Healthcare AI Hackathon Entry
> **Date:** 2026-03-14 (updated 2026-03-14 with full rules review)
> **Deadline:** May 11, 2026, 11:00 PM EDT (58 days)
> **Prize Pool:** $25,000 (13 prizes: $7.5K / $5K / $2.5K / 10x $1K)
> **Participants:** 745 registered
> **Status:** Design Approved — Spec Updated with Full Rules Compliance

---

## 0. Hackathon Compliance Checklist

**These are non-negotiable requirements. Missing ANY = disqualification.**

### Stage 1: Technical Qualification (Pass/Fail)
- [ ] Published to **Prompt Opinion Marketplace** with functional configuration
- [ ] Demonstrates explicit **MCP Server** implementation
- [ ] Discoverable and invokable within **Prompt Opinion Platform**
- [ ] Uses **exclusively synthetic or de-identified data** (NO real PHI)

### Submission Deliverables (ALL Required)
- [ ] Functioning project published to Prompt Opinion Marketplace
- [ ] Text description explaining features and functionality
- [ ] URL to published project in the Prompt Opinion Marketplace
- [ ] Demo video **under 3 minutes** showing project **inside Prompt Opinion platform**
- [ ] Video publicly available on YouTube, Vimeo, or Youku
- [ ] All materials in English

### Mandatory Technology
- [ ] **Prompt Opinion Platform** — must utilize and publish to marketplace
- [ ] **SHARP Extension Specs** — must implement healthcare context propagation:
  - `X-FHIR-Server-URL` header
  - `X-Patient-ID` header
  - `X-FHIR-Access-Token` header
  - Server advertises FHIR context requirements via `$.capabilities.experimental.fhir_context_required`
- [ ] **MCP Server** (Path A chosen) — explicit implementation required

### Data Safety
- [ ] CMS public data is de-identified aggregate data — **NOT PHI** — safe to use
- [ ] Synthea data is synthetic — safe to use
- [ ] FHIR credentials in A2A agents travel in message metadata, **never in LLM prompts**

### IP / Pre-Existing Code
- [ ] Pre-existing code IS allowed (confirmed in rules)
- [ ] Cherry-picking from inspection-intelligence is compliant
- [ ] All third-party SDKs/APIs properly licensed (open source)

### Key Links
- Main page: https://agents-assemble.devpost.com/
- Rules: https://agents-assemble.devpost.com/rules
- Resources: https://agents-assemble.devpost.com/resources
- Platform: https://app.promptopinion.ai
- SHARP spec: https://sharponmcp.com
- Reference MCP server: https://github.com/prompt-opinion/po-community-mcp
- Reference A2A agents (Python): https://github.com/prompt-opinion/po-adk-python
- Discord: https://discord.gg/JS2bZVruUg

---

## 1. Problem Statement

Healthcare systems managing multiple facilities must monitor quality metrics, readmission rates, safety events, and patient experience across all sites simultaneously. Today, quality officers spend hours in spreadsheets trying to spot problems before they become crises. No existing tool combines enterprise analytics with AI-powered narrative generation to proactively surface anomalies, detect equity disparities, and generate executive briefings.

## 2. Solution

**HealthPulse AI** is a healthcare performance intelligence agent that:

1. **Monitors quality** across 5,400+ US hospitals using real CMS data
2. **Detects anomalies** via Z-score analysis on mortality, readmissions, safety, and timeliness
3. **Identifies equity disparities** by correlating facility performance with community social vulnerability
4. **Benchmarks facilities** with side-by-side comparison and AI-generated comparative narratives
5. **Generates executive briefings** using Claude to synthesize analytics into actionable reports

All data flows through a Domo MCP server, making the analytics accessible to any MCP-compatible AI agent.

## 3. Architecture

### System Diagram

```
┌──────────────────────────────────────────────────────────────┐
│              Prompt Opinion Platform (REQUIRED)               │
│              Agent discoverable + invokable here              │
│                                                               │
│  User query ──► Platform LLM ──► HealthPulse MCP Server      │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │     HealthPulse MCP Server (Python)                   │    │
│  │     Published to Prompt Opinion Marketplace           │    │
│  │                                                       │    │
│  │  SHARP Context Propagation:                           │    │
│  │  ├─ X-FHIR-Server-URL    (received from platform)    │    │
│  │  ├─ X-Patient-ID         (received from platform)    │    │
│  │  ├─ X-FHIR-Access-Token  (received from platform)    │    │
│  │  └─ capabilities.experimental.fhir_context_required   │    │
│  │                                                       │    │
│  │  Tools:                                               │    │
│  │  ├─ quality_monitor    — Z-score anomaly detection    │    │
│  │  ├─ care_gap_finder    — Excess readmission/mortality │    │
│  │  ├─ equity_detector    — SVI + outcome correlation    │    │
│  │  ├─ facility_benchmark — Cross-facility comparison    │    │
│  │  └─ executive_briefing — Returns structured data for  │    │
│  │                          platform LLM to narrate      │    │
│  │                                                       │    │
│  │  Resources:                                           │    │
│  │  ├─ facilities         — 5,400+ hospital profiles     │    │
│  │  ├─ quality_measures   — Mortality, safety, process   │    │
│  │  ├─ readmissions       — HRRP excess ratios           │    │
│  │  └─ community_health   — SVI + county rankings        │    │
│  └────────┬────────────────────────────┬────────────────┘    │
│           │                            │                      │
│  ┌────────▼──────────┐    ┌───────────▼───────────────┐     │
│  │  Domo API Layer   │    │  FHIR MCP Server          │     │
│  │  (internal)       │    │  (Phase 2)                │     │
│  │                   │    │                            │     │
│  │  Domo Developer   │    │  HAPI FHIR (Docker)       │     │
│  │  Trial Instance   │    │  + Synthea pre-built data  │     │
│  │  7 datasets       │    │  ~5K patients              │     │
│  │  ~146K rows       │    │                            │     │
│  └───────────────────┘    └────────────────────────────┘     │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Next.js Dashboard (supplementary, NOT the demo)      │    │
│  │  Local development UI + architecture showcase         │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Technology | Required? |
|-----------|---------------|------------|-----------|
| **HealthPulse MCP Server** | 5 analytics tools + resources + SHARP headers | Python 3.11+, `mcp` SDK | **YES — primary deliverable** |
| **Domo API Layer** | OAuth, dataset query, schema fetch (internal to MCP server) | Python, `requests` | YES |
| **Prompt Opinion Marketplace** | Publishing, discovery, invocation of MCP server | Platform-native | **YES — submission requirement** |
| **SHARP Context** | Healthcare context propagation via HTTP headers | MCP protocol extension | **YES — mandatory** |
| **Next.js Dashboard** | Development UI, architecture showcase, supplementary demo | Next.js 16, TypeScript, Tailwind v4 | Nice-to-have |
| **FHIR MCP Server** | Patient-level drill-down (Phase 2) | Python, HAPI FHIR | Recommended |
| **Claude AI** | Briefing generation (in dashboard); platform LLM handles it in Prompt Opinion | Anthropic SDK | In dashboard only |

## 4. Data Architecture

### 4.1 Data Sources (All Public, Free)

| Source | Format | Rows | Update Frequency |
|--------|--------|------|-----------------|
| CMS Hospital General Info | CSV | 5,426 | Quarterly |
| CMS Complications & Deaths | CSV | 95,780 | Quarterly |
| CMS Readmissions (HRRP) | CSV | 18,330 | Annual |
| CMS HAC Reduction Program | CSV | 3,055 | Annual |
| CMS HCAHPS Patient Experience | CSV | 325,652 | Quarterly |
| CMS Timely & Effective Care | CSV | 138,129 | Quarterly |
| CMS Healthcare Assoc. Infections | CSV | 172,404 | Quarterly |
| CMS Unplanned Hospital Visits | CSV | 67,046 | Quarterly |
| CMS Medicare Spending/Beneficiary | CSV | 4,625 | Quarterly |
| County Health Rankings | CSV | ~3,000 | Annual |
| CDC Social Vulnerability Index | CSV | ~3,200 | Biennial |

### 4.2 Domo Datasets (Curated)

Raw CMS data is cleaned and loaded into 7 Domo datasets:

| Domo Dataset | Source(s) | Est. Rows | Key Columns |
|-------------|----------|-----------|-------------|
| `hp_facilities` | Hospital General Info | ~5,400 | facility_id, name, state, type, ownership, star_rating |
| `hp_quality_measures` | Complications & Deaths, Timely/Effective Care | ~50,000 | facility_id, measure_id, measure_name, score, compared_to_national |
| `hp_readmissions` | HRRP, Unplanned Visits | ~25,000 | facility_id, measure_name, excess_readmission_ratio, predicted_rate, expected_rate |
| `hp_safety` | HAC Reduction, HAI | ~20,000 | facility_id, measure_id, sir_score, z_score, payment_reduction |
| `hp_patient_experience` | HCAHPS (composite scores only) | ~30,000 | facility_id, hcahps_measure_id, star_rating, answer_percent |
| `hp_cost_efficiency` | MSPB Hospital, Spending by Claim | ~10,000 | facility_id, score, avg_spending_hospital, avg_spending_national |
| `hp_community_health` | County Health Rankings, CDC SVI | ~6,000 | county_fips, svi_score, uninsured_rate, poverty_rate, premature_death_rate |

**Total: ~146,000 rows across 7 datasets**

### 4.3 Data Loading Pipeline

```
CMS data.cms.gov ──► Download CSVs ──► Python/pandas cleanup ──► PyDomo upload ──► Domo datasets
                                              │
County Health Rankings ─────────────────────►─┘
CDC SVI ────────────────────────────────────►─┘
```

**Pipeline script:** `scripts/load_cms_data.py`
- Downloads CSVs from CMS data portal
- Cleans: removes footnote columns, normalizes column names, filters to key measures
- Resolves county FIPS codes using Census Bureau crosswalk (see 4.4)
- Uploads via PyDomo `ds_create()` / `ds_update()`

### 4.3.1 Filtering Criteria (addresses W2, W6, W7)

Row counts in 4.2 reflect intentional filtering:

**`hp_quality_measures` (~50K from ~234K source):**
- From Complications & Deaths: keep only `measure_id` in mortality group (AMI, HF, COPD, PN, Stroke, CABG) and PSI-90 composite. Drop component PSIs. (~18K rows)
- From Timely & Effective Care: keep only composite/key measures: ED throughput (`OP_18b`, `OP_22`), sepsis (`SEP_1`), stroke (`STK` measures), immunization (`IMM_3`). Drop redundant sub-measures. (~32K rows)
- Drop rows where `score` = "Not Available" or footnote-only

**`hp_readmissions` (~25K from ~85K source):**
- From HRRP: keep all 6 condition measures (~18K rows)
- From Unplanned Visits: keep only `READM_30` measures, drop outpatient revisit measures (~7K rows)

**`hp_safety` (~20K from ~175K source):**
- From HAC Reduction: keep all rows (3K, includes SIR and weighted Z-scores)
- From HAI: keep only facility-level SIR scores (filter `measure_id LIKE '%SIR%'`), drop predicted/observed detail rows (~17K rows)

**`hp_patient_experience` (~30K from ~326K source):**
- Keep only composite measure rows (`hcahps_measure_id` ending in `_COMP` or `_LINEAR` or `_STAR`)
- Drop individual question/answer breakdowns

### 4.4 Join Strategy & FIPS Code Resolution (addresses W5)

All CMS datasets share `facility_id` (CCN) as the primary key.

**County FIPS resolution:** CMS Hospital General Info has free-text `countyparish` (e.g., "LOS ANGELES") and `state` (e.g., "CA"). To join with CDC SVI and County Health Rankings (which use 5-digit FIPS codes):

1. Download Census Bureau county FIPS crosswalk: `data/reference/county_fips_crosswalk.csv`
   Source: https://www.census.gov/geographies/reference-files/time-series/geo/name-lookup-tables.html
2. Normalize county names in both datasets (uppercase, strip "COUNTY"/"PARISH", handle "ST."/"SAINT", "DEKALB"/"DE KALB")
3. Join on `(state_abbrev, normalized_county_name)` → `county_fips`
4. Add `county_fips` as a column to `hp_facilities` during ETL
5. Facilities that fail to match (~2-3%) get `county_fips = NULL` and are excluded from equity analysis

```
hp_facilities.facility_id ──► hp_quality_measures.facility_id
                           ──► hp_readmissions.facility_id
                           ──► hp_safety.facility_id
                           ──► hp_patient_experience.facility_id
                           ──► hp_cost_efficiency.facility_id

hp_facilities.county_fips ──► hp_community_health.county_fips
```

Since Domo SQL doesn't support JOINs, joins happen client-side in the MCP server after parallel queries.

## 5. MCP Server Design

### 5.0 SHARP Extension Specs (Mandatory)

The MCP server must implement SHARP context propagation per https://sharponmcp.com:

**Initialize response advertises FHIR context capability:**
```json
{
  "capabilities": {
    "experimental": {
      "fhir_context_required": { "value": false }
    }
  }
}
```

We set `fhir_context_required: false` because our primary tools (quality, gaps, equity, benchmark) operate on aggregate CMS data, not individual patient FHIR records. However, when FHIR headers ARE provided, the server passes them through to the FHIR MCP layer for patient drill-down (Phase 2).

**SHARP headers handled:**
- `X-FHIR-Server-URL` — stored in request context, forwarded to FHIR tools
- `X-Patient-ID` — stored in request context, used for patient-specific queries
- `X-FHIR-Access-Token` — stored in request context, NEVER logged or passed to LLM prompts

**Authentication:** Anonymous for aggregate tools; OAuth Client Credentials for Domo API access (server-side only).

### 5.1 Tools

#### `quality_monitor`
**Purpose:** Detect facilities with quality anomalies across mortality, readmissions, safety, and timeliness.

**Input:**
```json
{
  "state": "CA",           // optional, filter by state
  "measure_group": "mortality",  // mortality | readmission | safety | timeliness | all
  "threshold_sigma": 2.0   // Z-score threshold for anomaly flagging
}
```

**Output:** List of anomalies with facility name, measure, score, Z-score, national comparison, and severity (medium/high/critical).

**Implementation:** Query `hp_quality_measures` and `hp_safety`. The HAC Reduction dataset contains Standardized Infection Ratios (SIR) and weighted Z-scores for HAI measures (CLABSI, CAUTI, etc.) — these are used directly. For other measures (mortality rates, readmission rates, process measures), Z-scores are computed at query time from the population mean and standard deviation of each measure across all facilities.

#### `care_gap_finder`
**Purpose:** Identify facilities with excess readmission ratios, worse-than-national mortality, or other care gaps.

**Input:**
```json
{
  "state": "CA",           // optional
  "gap_type": "readmission", // readmission | mortality | safety | all
  "min_excess_ratio": 1.05  // threshold for excess readmission ratio
}
```

**Output:** List of facilities with gaps, ranked by severity. Includes excess ratios, predicted vs expected rates, discharge volume.

#### `equity_detector`
**Purpose:** Correlate facility quality outcomes with community social vulnerability.

**Input:**
```json
{
  "state": "CA",           // optional
  "svi_threshold": 0.75,   // SVI percentile threshold (0-1, higher = more vulnerable)
  "outcome_measure": "readmission"  // readmission | mortality | safety
}
```

**Output:** Facilities serving high-vulnerability communities with poor outcomes. Includes SVI score, uninsured rate, poverty rate, and the quality gap vs facilities in low-SVI communities.

#### `facility_benchmark`
**Purpose:** Compare two or more facilities across all quality dimensions.

**Input:**
```json
{
  "facility_ids": ["050454", "050625"],  // CMS CCN numbers
  "measures": ["mortality", "readmission", "safety", "patient_experience", "cost"]
}
```

**Output:** Side-by-side comparison with scores, national comparisons, and delta analysis.

#### `executive_briefing`
**Purpose:** Aggregate analytics across tools into a structured briefing payload. Does NOT call an LLM — returns structured data that the calling agent (Prompt Opinion platform LLM or our dashboard's Claude integration) uses to generate narrative.

**Design rationale (addresses W4):** Keeping the MCP server LLM-free eliminates the `ANTHROPIC_API_KEY` dependency from the server, avoids rate-limit conflicts with the platform's own LLM, and follows the MCP pattern where tools provide data and the host agent provides reasoning.

**Input:**
```json
{
  "scope": "state",        // state | facility | network
  "state": "CA",           // for state scope
  "facility_ids": [],      // for facility/network scope
  "include_equity": true
}
```

**Output:** Structured JSON with raw analytics data organized for narrative generation:
```json
{
  "summary_stats": { "total_facilities": 400, "anomaly_count": 12, "avg_star_rating": 3.2 },
  "anomalies": [{"facility": "", "measure": "", "z_score": 0, "severity": ""}],
  "care_gaps": [{"facility": "", "gap_type": "", "excess_ratio": 0}],
  "equity_flags": [{"facility": "", "svi_score": 0, "outcome_gap": ""}],
  "top_performers": [{"facility": "", "star_rating": 5}],
  "bottom_performers": [{"facility": "", "star_rating": 1}],
  "suggested_prompt": "You are a healthcare quality analyst. Based on the following data..."
}
```

The `suggested_prompt` field provides a ready-to-use system prompt that the platform LLM can use to generate the narrative. The Next.js dashboard uses its own Claude integration to generate briefings from this same structured data.

### 5.2 Resources

MCP resources expose read-only reference data:

| Resource URI | Description |
|-------------|-------------|
| `healthpulse://facilities` | All 5,400+ hospital profiles |
| `healthpulse://facilities/{id}` | Single facility detail |
| `healthpulse://measures/{group}` | Available quality measures by group |
| `healthpulse://states` | List of states with facility counts |

## 6. Dashboard UI

### Pages

| Page | Purpose | Cherry-Pick From |
|------|---------|-----------------|
| `/` | Login / landing | inspection-intelligence login |
| `/dashboard` | 6 KPI cards + anomaly alerts + pass/fail charts | inspection-intelligence dashboard |
| `/facilities` | Sortable facility table with quality scores, drill-down | inspection-intelligence stations |
| `/compare` | Side-by-side facility comparison + AI narrative | inspection-intelligence compare |
| `/equity` | SVI map + disparity analysis (new) | New component |
| `/briefing` | Executive briefing + PDF export | inspection-intelligence briefing |

### Cherry-Picked Components

| Component | Source | Adaptation |
|-----------|--------|------------|
| `DomoClient` | `inspection-intelligence/src/lib/data/domo-client.ts` | New credentials |
| `QueryEngine` | `inspection-intelligence/src/lib/data/domo-query.ts` | CMS measure queries |
| `KPIEngine` | `inspection-intelligence/src/lib/analytics/kpi-engine.ts` | Healthcare metrics |
| `AnomalyDetection` | Z-score logic in kpi-engine | Same math, medical thresholds |
| `BriefingGenerator` | `inspection-intelligence/src/lib/ai/briefing-generator.ts` | Healthcare prompts |
| `ComparisonPrompts` | `inspection-intelligence/src/lib/ai/comparison-prompts.ts` | Facility comparison |
| `RateLimiter` | `inspection-intelligence/src/lib/rate-limit.ts` | Drop-in |
| `BriefingPDF` | `inspection-intelligence/src/components/briefing/BriefingPDF.tsx` | Rebrand |
| `KPICards` | `inspection-intelligence/src/components/dashboard/KPICards.tsx` | New metrics |
| `DataProvider` | `inspection-intelligence/src/components/layout/DataProvider.tsx` | New data model |

## 7. AI Integration

### Briefing Generation

**Model:** Claude Sonnet 4 (claude-sonnet-4-20250514)
**Max tokens:** 4096

**System prompt pattern:**
```
You are a healthcare quality analyst for a hospital network.
Analyze the following quality metrics and generate an executive briefing.
Focus on actionable insights, not just data recitation.
Flag anomalies, equity concerns, and recommended interventions.
```

**Input structure:** Structured JSON with KPIs, anomalies, facility rankings, equity indicators.

**Output structure:**
```json
{
  "executive_summary": "string",
  "key_findings": ["string"],
  "anomalies_and_alerts": [{"facility": "", "measure": "", "severity": "", "detail": ""}],
  "equity_insights": ["string"],
  "recommended_actions": [{"priority": "", "action": "", "rationale": ""}]
}
```

**Rate limiting:** 10 requests/minute global, 24-hour cache per scope/state.

## 8. Authentication & Caching

### Domo API (Server-to-Server)
- OAuth client credentials flow (GET request, Basic auth)
- Token cached with 60-second safety buffer
- Scope: `data`

### Dashboard Auth
- Open access for hackathon — no login required
- Dashboard is supplementary to the MCP submission; security is not a judging criterion

### Caching Strategy (addresses N2)

| Layer | Cache | TTL | Storage |
|-------|-------|-----|---------|
| Domo OAuth token | Yes | ~3540s (token TTL minus 60s buffer) | In-memory |
| MCP tool results | Yes | 15 minutes per (tool, params) combo | In-memory dict |
| Executive briefing data | Yes | 1 hour per (scope, state) | In-memory dict |
| Dashboard Domo queries | Yes | 15 minutes per dataset | In-memory Map (cherry-picked from inspection-intelligence) |
| Dashboard AI briefings | Yes | 24 hours per scope | localStorage (client-side) |

CMS data updates quarterly — 15-minute server cache is more than sufficient.

## 9. Testing Strategy

| Layer | Framework | Focus |
|-------|-----------|-------|
| Data pipeline | pytest | CSV download, cleaning, Domo upload verification |
| MCP Server | pytest | Tool input/output contracts, anomaly detection math |
| Dashboard API routes | Vitest | Data endpoints, briefing generation |
| Analytics engine | Vitest | KPI calculations, Z-score math, threshold logic |
| AI prompts | Vitest | Prompt structure, output parsing |
| Components | Vitest | KPI cards, charts, tables render correctly |

**Target:** 200+ tests across all layers.

## 10. Project Structure

```
health-pulse/
├── scripts/
│   ├── load_cms_data.py          # Download + clean + upload CMS data to Domo
│   ├── load_community_data.py    # County Health Rankings + CDC SVI
│   ├── resolve_fips.py           # County name → FIPS code resolution
│   └── verify_datasets.py        # Verify Domo datasets are queryable
├── mcp-server/
│   ├── pyproject.toml
│   ├── src/
│   │   └── healthpulse_mcp/
│   │       ├── __init__.py
│   │       ├── server.py         # MCP server entry point + SHARP handler
│   │       ├── sharp.py          # SHARP context propagation (3 headers)
│   │       ├── tools/
│   │       │   ├── quality_monitor.py
│   │       │   ├── care_gap_finder.py
│   │       │   ├── equity_detector.py
│   │       │   ├── facility_benchmark.py
│   │       │   └── executive_briefing.py
│   │       ├── resources/
│   │       │   └── facilities.py
│   │       ├── domo_client.py    # Domo API wrapper (OAuth, query, schema)
│   │       └── analytics.py     # Z-score, anomaly detection
│   └── tests/
│       ├── test_quality_monitor.py
│       ├── test_care_gap_finder.py
│       ├── test_equity_detector.py
│       ├── test_analytics.py
│       ├── test_sharp.py         # SHARP header handling tests
│       └── conftest.py           # Fixtures with mock Domo data
├── web/
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── facilities/page.tsx
│   │   │   ├── compare/page.tsx
│   │   │   ├── equity/page.tsx
│   │   │   ├── briefing/page.tsx
│   │   │   └── api/
│   │   │       ├── data/route.ts
│   │   │       ├── briefing/route.ts
│   │   │       └── compare/route.ts
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   ├── dashboard/
│   │   │   ├── facilities/
│   │   │   ├── compare/
│   │   │   ├── equity/
│   │   │   └── briefing/
│   │   ├── lib/
│   │   │   ├── data/
│   │   │   │   ├── domo-client.ts
│   │   │   │   ├── domo-query.ts
│   │   │   │   └── types.ts
│   │   │   ├── analytics/
│   │   │   │   ├── kpi-engine.ts
│   │   │   │   └── anomaly-detection.ts
│   │   │   └── ai/
│   │   │       ├── briefing-generator.ts
│   │   │       └── prompts.ts
│   │   └── types/
│   │       └── index.ts
│   └── tests/
├── data/
│   ├── raw/                      # Downloaded CMS CSVs (gitignored)
│   └── reference/                # Census FIPS crosswalk (committed)
│       └── county_fips_crosswalk.csv
├── docs/
│   └── superpowers/specs/
├── assets/                       # Screenshots, architecture diagram for submission
├── CLAUDE.md
├── README.md
├── .env.example                  # DOMO_CLIENT_ID, DOMO_CLIENT_SECRET, ANTHROPIC_API_KEY
└── .gitignore                    # data/raw/, .env*, node_modules/, __pycache__/
```

### Environment Variables

```
# Domo Developer Trial
DOMO_CLIENT_ID=              # From Domo developer portal
DOMO_CLIENT_SECRET=          # From Domo developer portal
DOMO_INSTANCE=               # Trial instance name

# Anthropic (dashboard only, NOT in MCP server)
ANTHROPIC_API_KEY=           # For Next.js dashboard briefing generation

# Dataset IDs (populated after load_cms_data.py runs)
HP_FACILITIES_DATASET_ID=
HP_QUALITY_DATASET_ID=
HP_READMISSIONS_DATASET_ID=
HP_SAFETY_DATASET_ID=
HP_EXPERIENCE_DATASET_ID=
HP_COST_DATASET_ID=
HP_COMMUNITY_DATASET_ID=
```
```

## 11. Phased Delivery

**Critical sequencing change:** Prompt Opinion integration is Phase 1, not Phase 2. The demo video MUST show the solution working inside Prompt Opinion platform. The Next.js dashboard is supplementary.

### Phase 0: Platform Exploration + Data Foundation (Days 1-3)

- **Day 1:** Register on Prompt Opinion (https://app.promptopinion.ai), explore platform, study reference repos (`po-community-mcp`, `po-adk-python`), watch getting-started video
- **Day 1:** Sign up for Domo Developer Trial (https://www.domo.com/start/developer)
- **Day 2:** Download CMS CSVs (10 files), download Census FIPS crosswalk
- **Day 2-3:** Python cleanup script with FIPS resolution, PyDomo upload to 7 Domo datasets
- **Day 3:** Verify Domo queries work; deploy minimal "hello world" MCP server to Prompt Opinion to validate publishing flow

**Gate:** Can query all 7 Domo datasets AND have published a test MCP server to Prompt Opinion Marketplace.

### Phase 1a: MCP Server with SHARP (Days 4-10)

- Set up Python project with MCP SDK
- Implement SHARP context propagation (3 HTTP headers + capability advertisement)
- Implement Domo API client (OAuth, query, schema — adapted from inspection-intelligence)
- Implement analytics engine (Z-score computation, anomaly detection)
- Implement 5 MCP tools (quality_monitor, care_gap_finder, equity_detector, facility_benchmark, executive_briefing)
- Implement MCP resources (facilities, measures, states)
- Write tests (pytest) — mock Domo responses for unit tests, live Domo for integration tests
- Publish to Prompt Opinion Marketplace after each tool is working
- Test invocability within Prompt Opinion platform

**Gate:** All 5 tools return correct results when invoked through Prompt Opinion platform.

### Phase 1b: Dashboard (Days 8-14, overlaps with 1a)

- Initialize Next.js project (supplementary development UI)
- Cherry-pick components from inspection-intelligence
- Build pages: dashboard, facilities, compare, equity, briefing
- Wire up to Domo API directly (dashboard does NOT go through MCP)
- AI briefing integration (Claude Sonnet 4 via Anthropic SDK)
- Write tests (Vitest)

**Gate:** Dashboard working with real CMS data, AI briefings generating. (Supplementary to MCP submission.)

### Phase 2: FHIR Layer (Days 15-18)

- Deploy HAPI FHIR via Docker
- Download pre-built Synthea dataset, load into FHIR server
- Add FHIR-aware tools to MCP server (patient lookup, risk factors)
- When SHARP headers are present, use them for patient-level queries
- Update Prompt Opinion Marketplace publishing

**Gate:** Agent can answer "show me high-risk patients at facility X" when FHIR context is provided.

### Phase 3: Polish & Submit (Days 19-24)

- Record 3-minute demo video **inside Prompt Opinion platform**
- Upload to YouTube (publicly available)
- Write submission text explicitly addressing: AI Factor, Healthcare Impact, Feasibility
- Take screenshots of agent working in Prompt Opinion
- Create architecture diagram showing Domo MCP + SHARP + FHIR + Prompt Opinion
- Polish README with setup instructions
- Final testing pass — verify Stage 1 qualification checklist (Section 0)
- Submit on Devpost with: description, marketplace URL, video URL

**Gate:** All Section 0 checklist items checked. Submission complete.

### Buffer: 34 days before May 11 deadline

### Domo Trial Timing (addresses W1)

- Domo Developer Trial = 30 days, instant activation (no approval needed)
- Start trial: **April 11, 2026** (30 days before May 11 deadline)
- This gives us the trial active from Apr 11 through May 11
- We can start development locally with mock data / existing instance before Apr 11
- Fallback: `opusinspection` Domo instance (existing, working OAuth, prefix datasets with `hp_`)

## 12. Hackathon Submission Assets

| Asset | Required? | Description |
|-------|-----------|-------------|
| **Prompt Opinion Marketplace URL** | **YES** | Published, discoverable, invokable MCP server |
| **Demo video (< 3 min)** | **YES** | Screencast showing agent working **inside Prompt Opinion platform** |
| **Video hosting** | **YES** | YouTube, Vimeo, or Youku — publicly available |
| **Text description** | **YES** | Addresses AI Factor, Healthcare Impact, Feasibility explicitly |
| **Code repository** | **YES** | Clean, documented, production-quality |
| **Architecture diagram** | Recommended | Shows Domo MCP + SHARP + FHIR + Prompt Opinion |
| **README** | Recommended | Architecture, setup instructions, data sources, tech stack |
| **Screenshots** | Recommended | Agent in Prompt Opinion + supplementary dashboard views |

**Demo video must show:** The MCP server being invoked inside Prompt Opinion platform. NOT just a standalone dashboard demo. Show at least: quality anomaly detection, facility benchmark, equity analysis, and the structured briefing data being narrated by the platform LLM.

## 13. Judging Criteria Alignment

| Criterion | How HealthPulse Scores |
|-----------|----------------------|
| **AI Factor (1/3)** | Claude generates cross-cutting insights connecting quality anomalies to equity disparities to care gaps. AI produces narrative briefings that synthesize multi-dimensional data into actionable recommendations. Z-score anomaly detection surfaces patterns invisible in standard dashboards. |
| **Healthcare Impact (1/3)** | Addresses 3 CMS priorities: quality improvement, health equity, population health. Real CMS data for 5,400+ hospitals. Clear hypothesis: integrated intelligence prevents problems siloed dashboards miss. Judges from Mayo/Cleveland Clinic/CHOP will recognize the data and the problem. |
| **Feasibility (1/3)** | Uses only aggregate public data (no PHI). Domo MCP server is production-ready. Architecture mirrors real health system BI+EHR pattern. All code patterns proven across 5 states in inspection-intelligence (274 tests). |

## 14. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Domo trial expires before deadline | Low | High | Start trial Apr 11 (30 days). Instant activation. Fallback: existing `opusinspection` instance with `hp_` prefix. |
| Prompt Opinion platform is harder than expected | Medium | **Critical** | Moved to Phase 0/1 (not Phase 2). Explore on Day 1. Reference repos (`po-community-mcp`) provide working examples. Platform has no-code agent config option. |
| SHARP implementation is unclear | Medium | High | sharponmcp.com has spec. Reference MCP server (`po-community-mcp`) implements it. Study that implementation first. |
| CMS data has too many nulls | Low | Medium | Filter to ~3,000 hospitals with complete data. Still massive. |
| FHIR integration delayed | Medium | Low | Phase 2, non-critical. MCP Server qualifies without it. SHARP headers handled but forwarded to mock/stub. |
| Demo video doesn't show Prompt Opinion | Low | **Critical** | Demo MUST be recorded inside Prompt Opinion platform, not standalone dashboard. Plan recording session specifically. |
| County FIPS matching fails | Low | Medium | Census Bureau crosswalk handles 97%+ of counties. Remaining get NULL and are excluded from equity analysis only. |
| Marketplace publishing fails | Low | **Critical** | Test publish on Day 1 with hello-world MCP server. Unblock early. Contact support@promptopinion.ai if issues. |

## 15. Success Criteria

**Minimum Viable Submission (must achieve all):**
1. MCP server published to Prompt Opinion Marketplace
2. Discoverable and invokable within Prompt Opinion platform
3. SHARP headers handled per spec
4. At least 3 of 5 tools working with real CMS data
5. Demo video (< 3 min) recorded inside Prompt Opinion platform
6. Submission text addresses all 3 judging criteria
7. Uses only de-identified/synthetic data (zero PHI)

**Target (competitive entry):**
8. All 5 MCP tools returning meaningful results
9. FHIR patient drill-down working (Phase 2)
10. Supplementary Next.js dashboard deployed
11. 200+ tests passing
12. Architecture diagram and polished README
13. PDF briefing export from dashboard
