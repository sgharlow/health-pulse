# HealthPulse AI — Hackathon Submission

## Summary

HealthPulse AI is a production-deployed MCP server that gives AI agents five healthcare analytics tools backed by 233,000+ rows of real CMS hospital quality data across 5,400+ US facilities. It surfaces quality anomalies, care gaps, health equity disparities, facility benchmarks, and executive briefings — turning public data that exists today into AI-actionable intelligence that no traditional dashboard can deliver.

---

## The AI Factor

Traditional hospital quality dashboards display data. HealthPulse AI reasons about it.

**How generative AI solves problems traditional software cannot:**

- **Z-score anomaly detection across 5,400 hospitals simultaneously.** A conventional BI dashboard shows you a facility's readmission rate. HealthPulse AI computes the statistical distribution across every hospital in the dataset and surfaces the non-obvious outliers — facilities that look fine on absolute numbers but are 3+ standard deviations from peers. Running `quality_monitor(state="CA")` found 110 critical anomalies that a threshold-based alert would never catch.

- **Cross-cutting narrative intelligence.** The `executive_briefing` tool aggregates quality anomalies, readmission gaps, and equity indicators into a single structured object and generates a `suggested_prompt` the platform LLM uses to produce a cohesive narrative. This connects dots across three separate data domains — quality, operations, and social determinants — in a single reasoning step. No traditional BI tool chains these together automatically.

- **Equity analysis through correlation, not configuration.** The `equity_detector` correlates facility star ratings with county-level CDC Social Vulnerability Index scores at runtime. A human analyst configuring this join in a BI tool would take days. An AI agent calls one tool and gets the disparity gap between high-SVI and low-SVI facilities in seconds.

- **Conversational specificity.** An AI agent can ask "benchmark these 4 hospitals on AMI mortality" and get a structured comparison. The same question through a CMS website requires navigating multiple pages and manually tabulating results.

---

## Potential Impact

**The problem is measurable and costly:**

- Medicare readmission penalties cost US hospitals over **$500M annually** in CMS payment reductions. The underlying excess readmissions represent an estimated **$26B in annual Medicare costs**.
- CMS quality penalties (Value-Based Purchasing, Hospital Acquired Condition Reduction Program) affect nearly every US hospital — but identifying which facilities are at risk requires analysis most health systems don't have the data science capacity to run continuously.
- The CDC estimates **100,000+ preventable deaths annually** from patient safety events — the same events captured in the PSI and HAI measures HealthPulse AI monitors.
- Health equity mandates are expanding across state and federal payers, yet most health systems lack tools to systematically measure the disparity between outcomes in high- and low-vulnerability communities.

**What HealthPulse AI found on real data:**

- 110 critical anomalies (Z-score ≥ 3.0) in California alone using `quality_monitor`.
- Facilities in high-SVI counties (top quartile of social vulnerability) show measurable star-rating gaps compared to low-SVI facilities — a disparity invisible in facility-level reporting.
- Care gaps (excess readmission ratio > 1.05) are distributed unevenly across states and hospital types in ways that aggregate national statistics obscure.

**Who uses this:**

- **Health system CMOs and CNOs** running quality improvement programs need anomaly detection at scale, not manual chart review.
- **Value-based care teams** managing ACO or bundled payment contracts need to identify readmission risk across their network.
- **Health equity officers** need systematic, data-driven evidence of disparities to satisfy CMS and state mandates.
- **Healthcare consultants and payers** benchmarking facility performance need comparable, standardized metrics.

All of these users already interact with AI assistants. HealthPulse AI puts the right data tools in front of those assistants.

---

## Feasibility

HealthPulse AI is not a proof of concept — it is operational today.

**Why it can exist in real healthcare right now:**

- **No PHI.** Every data point comes from CMS public datasets and the CDC Social Vulnerability Index — all de-identified aggregate statistics. There is no HIPAA barrier to deployment. The data is already public; HealthPulse AI makes it queryable by AI agents.

- **Domo is already in thousands of health systems.** Domo is one of the most widely deployed BI platforms in healthcare. The data pipeline (`scripts/load_cms_data.py`) loads standard CMS CSV exports into Domo datasets. Health systems that already use Domo can point HealthPulse AI at their existing CMS data with environment variable changes only.

- **SHARP and MCP are open standards.** The SHARP-on-MCP specification (`sharponmcp.com`) provides a standard way to propagate FHIR context through MCP headers. HealthPulse AI implements SHARP today, meaning future FHIR-aware enhancements (e.g., patient-level context from an EHR) can be added without changing the server contract.

- **Architecture mirrors real healthcare BI + EHR patterns.** The pattern of a middleware server sitting between an AI platform and a clinical data warehouse is exactly how health systems are building AI-enabled workflows today. HealthPulse AI provides a reference implementation of that pattern using open standards.

- **Production-grade engineering:**
  - 80+ unit tests covering all 5 tools, analytics engine, SHARP context, and Domo client
  - Docker deployment on Railway with public HTTPS endpoint
  - API key authentication middleware
  - Stateless HTTP transport (horizontally scalable)
  - No LLM calls inside the server — tools return structured data for the platform LLM to reason over, avoiding latency and cost cascades

---

## Technical Details

**MCP Server**
- 5 tools: `quality_monitor`, `care_gap_finder`, `equity_detector`, `facility_benchmark`, `executive_briefing`
- SHARP context propagation via `X-FHIR-Server-URL`, `X-Patient-ID`, `X-FHIR-Access-Token` headers
- Streamable HTTP transport, stateless mode (FastMCP)
- Optional API key authentication
- Language: Python 3.11; framework: FastMCP + Starlette + uvicorn

**Data**
- 233,000+ rows of real CMS data across 7 Domo datasets
- 5,400+ US hospitals covered
- Data sources: CMS Hospital General Information, Quality Measures, Readmission & Death Measures, HCAHPS, Timely & Effective Care, Complications & Deaths; CDC Social Vulnerability Index

**Analytics**
- Z-score anomaly detection with severity classification (`critical` ≥ 3.0σ, `high` ≥ 2.5σ, `medium` ≥ 2.0σ)
- Statistical disparity analysis: mean star-rating comparison between high-SVI and low-SVI facility populations
- Excess readmission ratio thresholding with configurable sensitivity

**Tests**
- 80+ unit tests
- Test files: `test_analytics.py`, `test_quality_monitor.py`, `test_care_gap_finder.py`, `test_equity_detector.py`, `test_facility_benchmark.py`, `test_executive_briefing.py`, `test_domo_client.py`, `test_sharp.py`, `test_integration.py`
- All tests pass with mocked Domo responses (no live API calls required in CI)

**Deployment**
- Docker container on Railway
- Public HTTPS endpoint: `https://health-pulse-mcp-production.up.railway.app/mcp`
- Registered on Prompt Opinion marketplace

**Supplementary**
- Next.js 16 dashboard for development and demo visualization
- GitHub: `https://github.com/sgharlow/health-pulse`
