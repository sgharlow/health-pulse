# HealthPulse AI — Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      THREE ACCESS POINTS                            │
│                                                                     │
│  1. PROMPT OPINION         2. NEXT.JS DASHBOARD    3. CHAT          │
│     MARKETPLACE               (Vercel)             INTERFACE        │
│                                                                     │
│  User asks question        8 analytics pages       Conversational   │
│  in natural language       + AI briefing           tool routing     │
│       │                    + PDF export            via Claude SDK    │
│       │                         │                       │           │
│       └─────────────┬───────────┴───────────────────────┘           │
│                     │                                               │
│              ┌──────▼──────┐                                        │
│              │  Tool Call  │                                         │
│              │  via MCP    │                                         │
│              └──────┬──────┘                                        │
│                     │                                               │
└─────────────────────┼───────────────────────────────────────────────┘
                      │ HTTPS (Streamable HTTP)
                      │ + SHARP Headers
                      │   X-FHIR-Server-URL
                      │   X-Patient-ID
                      │   X-FHIR-Access-Token
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│              HEALTHPULSE MCP SERVER (Railway)                        │
│              https://health-pulse-mcp-production.up.railway.app      │
│                                                                     │
│  ┌─── API Key Auth ───┐  ┌─── SHARP Middleware ───┐                │
│  │  X-API-Key header   │  │  Extract FHIR context  │                │
│  └─────────────────────┘  └────────────────────────┘                │
│                                                                     │
│  ┌─────────── 11 MCP Tools (grouped by category) ──────────┐      │
│  │                                                           │      │
│  │  QUALITY + SAFETY                                         │      │
│  │    quality_monitor        Z-score anomaly detection        │      │
│  │    care_gap_finder        Excess readmission/mortality     │      │
│  │    cross_cutting_analysis Multi-factor compounding risk    │      │
│  │                                                           │      │
│  │  EQUITY + EXPERIENCE                                      │      │
│  │    equity_detector        SVI + outcome correlation        │      │
│  │    patient_experience     HCAHPS survey dimensional        │      │
│  │                                                           │      │
│  │  BENCHMARKING + RANKING                                   │      │
│  │    facility_benchmark     Cross-facility comparison        │      │
│  │    state_ranking          Composite state performance      │      │
│  │    cost_efficiency        Spending-quality correlation     │      │
│  │                                                           │      │
│  │  PATIENT-LEVEL (FHIR)                                     │      │
│  │    patient_risk_profile   Individual risk assessment       │      │
│  │    patient_cohort_analysis Population health trends        │      │
│  │                                                           │      │
│  │  EXECUTIVE                                                │      │
│  │    executive_briefing     Structured AI narrative data     │      │
│  │                                                           │      │
│  └──────────────────────┬────────────────────────────────────┘      │
│                         │                                            │
│  ┌──── Analytics ───────┤  ┌──── Resources ──────────────┐         │
│  │  Z-score computation │  │  4 static + 2 URI templates │         │
│  │  Severity classify   │  │  (6 total MCP resources)    │         │
│  │  Cross-cutting agg   │  └─────────────────────────────┘         │
│  │  Input validation    │                                           │
│  └──────────────────────┘                                           │
│                         │                                            │
└────────┬────────────────┼────────────────────────────────────────────┘
         │                │ OAuth 2.0 (Client Credentials)
         │                ▼
         │  ┌─────────────────────────────────────────────────────────┐
         │  │                    DOMO PLATFORM                         │
         │  │                    (Data Layer)                          │
         │  │                                                         │
         │  │  ┌──────────────────────────────────────────────────┐  │
         │  │  │               7 Curated Datasets                  │  │
         │  │  │                                                   │  │
         │  │  │  hp_facilities          5,426 hospitals           │  │
         │  │  │  hp_quality_measures   29,765 quality metrics     │  │
         │  │  │  hp_readmissions       47,064 readmission rates   │  │
         │  │  │  hp_safety             31,789 safety measures     │  │
         │  │  │  hp_patient_experience 114,936 HCAHPS surveys     │  │
         │  │  │  hp_cost_efficiency      4,625 Medicare spending  │  │
         │  │  │  hp_community_health     2,408 county SVI         │  │
         │  │  │                                                   │  │
         │  │  │  Total: 233,605 rows of REAL CMS data             │  │
         │  │  └──────────────────────────────────────────────────┘  │
         │  │                                                         │
         │  └─────────────────────────────────────────────────────────┘
         │
         │  FHIR/Synthea Data (local)
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   SYNTHEA FHIR PATIENT LAYER                        │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │              100 Synthetic Patients                        │      │
│  │              1,002 FHIR Resources                         │      │
│  │                                                           │      │
│  │  Patient        Demographics, identifiers                 │      │
│  │  Condition      Active/resolved diagnoses                 │      │
│  │  MedicationRequest  Current medications                   │      │
│  │  Encounter      Hospital visits, ED visits                │      │
│  │  Observation    Lab results, vital signs                   │      │
│  │                                                           │      │
│  │  Used by: patient_risk_profile, patient_cohort_analysis   │      │
│  │  Context: SHARP headers propagate patient ID per-request  │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                      ▲
                      │ ETL Pipeline (Python + PyDomo)
                      │
┌─────────────────────┴───────────────────────────────────────────────┐
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
3. **Synthea** generates 100 synthetic FHIR patients with realistic clinical histories
4. **Domo** stores 233K+ rows across 7 curated datasets with SQL query API
5. **HealthPulse MCP Server** queries Domo and FHIR data, runs analytics (Z-score, cross-cutting, cohort), returns structured results
6. **Three access points** consume MCP tools:
   - Prompt Opinion Platform invokes tools via Streamable HTTP
   - Next.js Dashboard visualizes results across 8 pages with AI briefing and PDF export
   - Chat Interface routes natural language to tools via Claude SDK
7. **User** asks questions in natural language, gets data-driven healthcare intelligence

## Key Standards

- **MCP** (Model Context Protocol) — Tool registration, discovery, invocation (11 tools, 6 resources)
- **SHARP** — Healthcare context propagation (FHIR server URL, patient ID, access token)
- **FHIR** — Patient data model (Synthea-generated, EHR-ready)
- **Streamable HTTP** — Stateless HTTP transport for MCP server
- **CMS CCN** — 6-digit facility identifier used across all datasets

## Key Stats

| Metric | Value |
|--------|-------|
| MCP Tools | 11 |
| MCP Resources | 6 (4 static + 2 URI templates) |
| Domo Datasets | 7 (233K+ rows) |
| Synthetic FHIR Patients | 100 (1,002 resources) |
| CMS Hospitals | 5,426 |
| Tests | 275+ (212 MCP + 63 web) |
| Dashboard Pages | 8 |
| API Routes | 6 |
