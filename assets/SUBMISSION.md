# HealthPulse AI — Hackathon Submission

## Summary

HealthPulse AI is a production-deployed MCP server and interactive dashboard that gives AI agents eleven healthcare analytics tools backed by 233,000+ rows of real CMS hospital quality data across 5,400+ US facilities and 100 synthetic FHIR patients. It spans quality anomaly detection, care gap identification, health equity analysis, facility benchmarking, executive briefings, state performance rankings, cross-cutting multi-factor risk analysis, patient-level risk profiling, cohort analysis, HCAHPS patient experience scoring, and Medicare cost efficiency analysis — with a conversational chat interface, AI narrative briefing generation, and PDF export. This turns public data that exists today into AI-actionable intelligence that no traditional dashboard can deliver.

---

## The AI Factor

Traditional hospital quality dashboards display data. HealthPulse AI reasons about it — across 11 tools, 6 analytical dimensions, and two data layers (population-level CMS and patient-level FHIR).

**How generative AI solves problems traditional software cannot:**

- **Z-score anomaly detection across 5,400 hospitals simultaneously.** A conventional BI dashboard shows you a facility's readmission rate. HealthPulse AI computes the statistical distribution across every hospital in the dataset and surfaces the non-obvious outliers — facilities that look fine on absolute numbers but are 3+ standard deviations from peers. Running `quality_monitor(state="CA")` found 110 critical anomalies that a threshold-based alert would never catch.

- **Cross-cutting analysis spanning 6 dimensions.** The `cross_cutting_analysis` tool now evaluates facilities across quality anomalies, excess readmissions, equity indicators, patient experience ratings, cost efficiency, and star ratings simultaneously. In Florida alone, 94 of 222 hospitals (42%) have 2+ compounding risk factors. This multi-dimensional pattern detection — correlating clinical quality with patient satisfaction with spending efficiency — is impossible with traditional rule-based dashboards.

- **Patient-level drill-down from population analytics.** The `patient_risk_profile` and `patient_cohort_analysis` tools demonstrate how FHIR integration bridges the gap between facility-level analytics and individual care. An agent can move from "show me high-risk hospitals in Texas" to "show me this patient's risk profile" in a single conversation. 100 synthetic FHIR patients (1,002 resources) prove the pattern works end-to-end with SHARP header propagation.

- **Conversational AI with tool routing.** The dashboard chat interface uses the Anthropic SDK to route natural language questions to the appropriate MCP tool. A user types "compare UCSF with NYU Langone on mortality" and Claude selects `facility_benchmark`, calls it, and returns structured results with contextual narrative — no manual tool selection required.

- **AI narrative briefing generation.** The executive briefing page aggregates data from multiple tools and generates a cohesive narrative. The `suggested_prompt` field from `executive_briefing` feeds directly into Claude to produce board-ready summaries, with PDF export for offline sharing via `@react-pdf/renderer`.

- **HCAHPS patient experience analysis.** The `patient_experience` tool surfaces how patients actually rate their care — communication, responsiveness, environment, discharge planning — from real CMS survey data. This is the patient's voice in the analytics, a dimension that clinical quality metrics alone miss entirely.

- **Medicare cost-quality correlation.** The `cost_efficiency` tool identifies facilities delivering high-quality care at lower cost and those with spending-quality misalignment. It answers the question payers and policy makers care about most: where is money being spent well, and where is it being wasted?

- **Equity analysis through correlation, not configuration.** The `equity_detector` correlates facility star ratings with county-level CDC Social Vulnerability Index scores at runtime. A human analyst configuring this join in a BI tool would take days. An AI agent calls one tool and gets the disparity gap between high-SVI and low-SVI facilities in seconds.

---

## Potential Impact

**The problem is measurable and costly:**

- Medicare readmission penalties cost US hospitals over **$500M annually** in CMS payment reductions. The underlying excess readmissions represent an estimated **$26B in annual Medicare costs**.
- CMS quality penalties (Value-Based Purchasing, Hospital Acquired Condition Reduction Program) affect nearly every US hospital — but identifying which facilities are at risk requires analysis most health systems don't have the data science capacity to run continuously.
- The CDC estimates **100,000+ preventable deaths annually** from patient safety events — the same events captured in the PSI and HAI measures HealthPulse AI monitors.
- Health equity mandates are expanding across state and federal payers, yet most health systems lack tools to systematically measure the disparity between outcomes in high- and low-vulnerability communities.
- **HCAHPS scores directly affect CMS reimbursement** through the Value-Based Purchasing program — yet most systems analyze patient experience in isolation from clinical quality and cost data. HealthPulse AI connects all three.

**What HealthPulse AI found on real data:**

- 110 critical anomalies (Z-score >= 3.0) in California alone using `quality_monitor`.
- Facilities in high-SVI counties (top quartile of social vulnerability) show measurable star-rating gaps compared to low-SVI facilities — a disparity invisible in facility-level reporting.
- Care gaps (excess readmission ratio > 1.05) are distributed unevenly across states and hospital types in ways that aggregate national statistics obscure.
- HCAHPS patient experience scores reveal communication and discharge planning gaps that correlate with readmission rates — connecting patient voice to clinical outcomes.
- Medicare spending analysis reveals facilities achieving 4+ star ratings at below-median cost, proving that quality and efficiency are not inherently at odds.

**Who uses this:**

- **Health system CMOs and CNOs** running quality improvement programs need anomaly detection at scale, not manual chart review.
- **Value-based care teams** managing ACO or bundled payment contracts need to identify readmission risk across their network.
- **Health equity officers** need systematic, data-driven evidence of disparities to satisfy CMS and state mandates.
- **Healthcare consultants and payers** benchmarking facility performance need comparable, standardized metrics.
- **Patient experience directors** need to connect HCAHPS survey data to clinical outcomes and identify actionable improvement areas.

All of these users already interact with AI assistants. HealthPulse AI puts the right data tools in front of those assistants — through the Prompt Opinion marketplace, a visual dashboard hub, and a conversational chat interface.

---

## Feasibility

HealthPulse AI is not a proof of concept — it is operational today with a unified hub connecting three access modalities.

**Why it can exist in real healthcare right now:**

- **No PHI.** Every data point comes from CMS public datasets and the CDC Social Vulnerability Index — all de-identified aggregate statistics. Synthea patient data is fully synthetic. There is no HIPAA barrier to deployment. The data is already public; HealthPulse AI makes it queryable by AI agents.

- **Domo is already in thousands of health systems.** Domo is one of the most widely deployed BI platforms in healthcare. The data pipeline (`scripts/load_cms_data.py`) loads standard CMS CSV exports into Domo datasets. Health systems that already use Domo can point HealthPulse AI at their existing CMS data with environment variable changes only.

- **SHARP and MCP are open standards.** The SHARP-on-MCP specification (`sharponmcp.com`) provides a standard way to propagate FHIR context through MCP headers. HealthPulse AI implements SHARP today with synthetic FHIR data, meaning the same tools work with real EHR integrations by changing the FHIR endpoint.

- **Architecture mirrors real healthcare BI + EHR patterns.** The pattern of a middleware server sitting between an AI platform and a clinical data warehouse is exactly how health systems are building AI-enabled workflows today. HealthPulse AI provides a reference implementation of that pattern using open standards.

- **Production-grade engineering:**
  - 313 tests (250 MCP server pytest + 63 web dashboard Vitest) covering all 11 tools, analytics engine, SHARP context, Domo client, API routes, and UI components
  - Docker deployment on Railway with public HTTPS endpoint (MCP server)
  - Vercel deployment with public URL (Next.js dashboard)
  - API key authentication middleware
  - Stateless HTTP transport (horizontally scalable)
  - No LLM calls inside the MCP server — tools return structured data for the platform LLM to reason over, avoiding latency and cost cascades

- **Unified access hub:**
  - Prompt Opinion marketplace for MCP tool invocation
  - Next.js dashboard with 7 pages of visual analytics
  - Conversational chat interface with Claude tool routing
  - AI narrative briefing generation with PDF export
  - All three access points backed by the same 11 MCP tools and real data

---

## Technical Details

**MCP Server**
- 11 tools: `quality_monitor`, `care_gap_finder`, `equity_detector`, `facility_benchmark`, `executive_briefing`, `state_ranking`, `cross_cutting_analysis`, `patient_risk_profile`, `patient_cohort_analysis`, `patient_experience`, `cost_efficiency`
- 6 MCP resources (4 static + 2 URI templates)
- SHARP context propagation via `X-FHIR-Server-URL`, `X-Patient-ID`, `X-FHIR-Access-Token` headers
- Streamable HTTP transport, stateless mode (FastMCP)
- Optional API key authentication
- Language: Python 3.11; framework: FastMCP + Starlette + uvicorn

**Data**
- 233,000+ rows of real CMS data across 7 Domo datasets
- 5,426 US hospitals covered
- 100 synthetic FHIR patients (1,002 resources) from Synthea
- Data sources: CMS Hospital General Information, Quality Measures, Readmission & Death Measures, HCAHPS, Timely & Effective Care, Complications & Deaths; CDC Social Vulnerability Index; Synthea FHIR bundles

**Dashboard**
- Next.js 16, TypeScript, Tailwind CSS, Recharts
- 7 pages: Hub, Quality Overview, Equity Analysis, Patient Experience, Cost Efficiency, Executive Briefing, Chat Interface, State Rankings
- 6 API routes connecting to MCP server
- Claude-powered chat interface with tool routing (@anthropic-ai/sdk)
- AI narrative briefing generation
- PDF export via @react-pdf/renderer

**FHIR/Synthea Integration**
- 100 synthetic patients generated by Synthea
- 1,002 FHIR resources (Patient, Condition, MedicationRequest, Encounter, Observation)
- SHARP header propagation on every MCP request
- `patient_risk_profile` generates individual risk assessments from FHIR data
- `patient_cohort_analysis` enables population health analysis across patient groups

**Analytics**
- Z-score anomaly detection with severity classification (`critical` >= 3.0 sigma, `high` >= 2.5 sigma, `medium` >= 2.0 sigma)
- Statistical disparity analysis: mean star-rating comparison between high-SVI and low-SVI facility populations
- Excess readmission ratio thresholding with configurable sensitivity
- Composite state scoring and cross-cutting multi-factor risk aggregation (6 dimensions)
- HCAHPS patient experience dimensional analysis
- Medicare spending-quality correlation and efficiency scoring
- Patient-level risk profiling from FHIR clinical data

**Tests**
- 313 tests (250 MCP server + 63 web dashboard)
- MCP test files: `test_analytics.py`, `test_quality_monitor.py`, `test_care_gap_finder.py`, `test_equity_detector.py`, `test_facility_benchmark.py`, `test_executive_briefing.py`, `test_state_ranking.py`, `test_cross_cutting.py`, `test_validation.py`, `test_domo_client.py`, `test_sharp.py`, `test_integration.py`, `test_patient_risk_profile.py`, `test_patient_cohort.py`, `test_patient_experience.py`, `test_cost_efficiency.py`
- Web tests: Vitest with component, API route, and integration tests
- All tests pass with mocked Domo responses (no live API calls required in CI)

**Deployment**
- MCP Server: Docker container on Railway — `https://health-pulse-mcp-production.up.railway.app/mcp`
- Dashboard: Next.js on Vercel — `https://web-umber-alpha-41.vercel.app`
- Registered on Prompt Opinion marketplace
- GitHub: `https://github.com/sgharlow/health-pulse`
