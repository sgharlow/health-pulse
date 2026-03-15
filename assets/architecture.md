# HealthPulse AI — Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PROMPT OPINION PLATFORM                         │
│                                                                     │
│   User: "Check for quality anomalies in California hospitals"       │
│                          │                                          │
│                     Platform LLM                                    │
│                    (Tool Selection)                                  │
│                          │                                          │
│                   ┌──────▼──────┐                                   │
│                   │  Tool Call  │                                    │
│                   │  via MCP    │                                    │
│                   └──────┬──────┘                                   │
│                          │                                          │
└──────────────────────────┼──────────────────────────────────────────┘
                           │ HTTPS (Streamable HTTP)
                           │ + SHARP Headers
                           │   X-FHIR-Server-URL
                           │   X-Patient-ID
                           │   X-FHIR-Access-Token
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│              HEALTHPULSE MCP SERVER (Railway)                       │
│              https://health-pulse-mcp-production.up.railway.app     │
│                                                                     │
│  ┌─── API Key Auth ───┐  ┌─── SHARP Middleware ───┐                │
│  │  X-API-Key header   │  │  Extract FHIR context  │                │
│  └─────────────────────┘  └────────────────────────┘                │
│                                                                     │
│  ┌─────────────────── 7 MCP Tools ──────────────────────────┐      │
│  │                                                           │      │
│  │  quality_monitor        Z-score anomaly detection         │      │
│  │  care_gap_finder        Excess readmission/mortality gaps │      │
│  │  equity_detector        SVI + outcome correlation         │      │
│  │  facility_benchmark     Cross-facility comparison         │      │
│  │  executive_briefing     Structured data for AI narrative  │      │
│  │  state_ranking          Composite state performance rank  │      │
│  │  cross_cutting_analysis Multi-factor compounding risk     │      │
│  │                                                           │      │
│  └──────────────────────┬────────────────────────────────────┘      │
│                         │                                            │
│  ┌──── Analytics ───────┤                                           │
│  │  Z-score computation │                                           │
│  │  Severity classify   │                                           │
│  │  Input validation    │                                           │
│  └──────────────────────┘                                           │
│                         │                                            │
└─────────────────────────┼────────────────────────────────────────────┘
                          │ OAuth 2.0 (Client Credentials)
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DOMO PLATFORM                                │
│                        (Data Layer)                                  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                   7 Curated Datasets                      │      │
│  │                                                           │      │
│  │  hp_facilities          5,426 hospitals (12 cols)         │      │
│  │  hp_quality_measures   29,765 quality metrics             │      │
│  │  hp_readmissions       47,064 readmission rates           │      │
│  │  hp_safety             31,789 HAC/HAI safety measures     │      │
│  │  hp_patient_experience 114,936 HCAHPS survey results      │      │
│  │  hp_cost_efficiency      4,625 Medicare spending          │      │
│  │  hp_community_health     2,408 county-level SVI           │      │
│  │                                                           │      │
│  │  Total: 233,605 rows of REAL CMS data                     │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                          ▲
                          │ ETL Pipeline (Python + PyDomo)
                          │
┌─────────────────────────┴───────────────────────────────────────────┐
│                     CMS PUBLIC DATA                                  │
│                     (data.cms.gov)                                   │
│                                                                     │
│  Hospital General Info      │  HCAHPS Patient Experience            │
│  Complications & Deaths     │  Healthcare Assoc. Infections         │
│  Readmissions (HRRP)        │  Unplanned Hospital Visits            │
│  HAC Reduction Program      │  Medicare Spending/Beneficiary        │
│  Timely & Effective Care    │  CDC Social Vulnerability Index       │
│                                                                     │
│  All public, de-identified, quarterly updates, free                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

1. **CMS publishes** quarterly hospital quality data at data.cms.gov
2. **ETL pipeline** downloads CSVs, cleans/filters, resolves county FIPS codes, uploads to Domo
3. **Domo** stores 233K+ rows across 7 curated datasets with SQL query API
4. **HealthPulse MCP Server** queries Domo, runs Z-score anomaly detection, returns structured results
5. **Prompt Opinion Platform** invokes MCP tools via Streamable HTTP, generates AI narratives
6. **User** asks questions in natural language, gets data-driven healthcare intelligence

## Key Standards

- **MCP** (Model Context Protocol) — Tool registration, discovery, invocation
- **SHARP** — Healthcare context propagation (FHIR server URL, patient ID, access token)
- **Streamable HTTP** — Stateless HTTP transport for MCP server
- **CMS CCN** — 6-digit facility identifier used across all datasets
