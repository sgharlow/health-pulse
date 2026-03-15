# HealthPulse AI — Remaining Steps to Submission

> Last updated: 2026-03-15
> Deadline: May 11, 2026, 11:00 PM EDT (57 days remaining)
> All code/data/deployment work is complete. Only manual steps remain.

---

## Pre-Submission Checklist

### ~~1. Disable Vercel Deployment Protection~~ DONE
SSO protection disabled via Vercel API on 2026-03-15. Dashboard is publicly accessible.

---

### 2. Verify Prompt Opinion Marketplace Publishing
**Time:** 5 minutes
**Why:** Stage 1 qualification requires the MCP server to be published, discoverable, and invokable.

1. Go to https://app.promptopinion.ai
2. Navigate to **Marketplace Studio** > **MCP Servers**
3. Confirm **HealthPulse AI** shows with **Published** toggle **ON**
4. Copy the marketplace URL (you'll need it for Devpost submission)
5. Navigate to **Launchpad** > select **HealthPulse AI** agent
6. Send a test query: `"Check for quality anomalies in Texas hospitals"`
7. Verify the agent responds with real data (tool call visible, anomalies listed)

---

### 3. Record Demo Video (Under 3 Minutes)
**Time:** 1-2 hours (including retakes)
**Why:** Required submission deliverable. Must show the project working inside Prompt Opinion platform.

#### Setup
- Use screen recording software (OBS, Loom, or Windows Game Bar: Win+G)
- Set browser to Prompt Opinion at 1920x1080 resolution
- Enable "Show Tool calls" toggle in the chat interface
- Close other tabs/notifications

#### Script

**[0:00-0:15] Introduction**
"HealthPulse AI is a healthcare performance intelligence platform with 11 MCP tools that monitors quality metrics, detects anomalies, identifies equity disparities, analyzes patient experience, benchmarks cost efficiency, and profiles patient risk across 5,400 US hospitals — powered by real CMS data, synthetic FHIR patients, and Domo analytics."

**[0:15-0:50] Quality Anomaly Detection**
Type: `Show me quality anomalies in California hospitals`
- Wait for response — agent calls `quality_monitor`
- Briefly highlight: number of anomalies, a critical finding (Z-score, facility name)

**[0:50-1:20] Cross-Cutting Multi-Factor Analysis**
Type: `Find facilities in Florida with multiple compounding concerns`
- Wait for response — agent calls `cross_cutting_analysis`
- Highlight: "94 of 222 Florida hospitals have 2+ simultaneous concerns"
- Point out a facility with quality + readmission + equity issues together

**[1:20-1:45] Patient Experience Analysis**
Type: `How do patients rate hospital care in New York?`
- Wait for response — agent calls `patient_experience`
- Highlight: HCAHPS dimensions — communication, responsiveness, discharge planning scores

**[1:45-2:10] Health Equity + Cost Efficiency**
Type: `Check for equity disparities and cost efficiency in Texas hospitals`
- Wait for response — agent calls `equity_detector` and/or `cost_efficiency`
- Highlight: real CDC SVI data, spending-quality correlation

**[2:10-2:30] Patient Risk Profile**
Type: `Show me the risk profile for patient Aaron697`
- Wait for response — agent calls `patient_risk_profile`
- Highlight: FHIR patient data — conditions, medications, risk factors from synthetic Synthea data

**[2:30-2:50] Facility Benchmark + State Ranking**
Type: `Compare UCSF Medical Center (050454) with NYU Langone (330214) and show me the worst-performing states`
- Wait for response — agent calls `facility_benchmark` and `state_ranking`
- Highlight: side-by-side quality measures, state composite scores

**[2:50-3:00] Closing**
"HealthPulse AI — 11 MCP tools, 233,000 rows of real CMS data, 100 synthetic FHIR patients, CDC Social Vulnerability Index, HCAHPS patient experience, Medicare cost analysis, SHARP healthcare context, conversational AI chat, and PDF export — deployed on Prompt Opinion, Railway, and Vercel."

#### Tips
- Keep queries short — the agent needs time to call tools and respond
- If a response is slow, you can speed up the video slightly in editing
- Speak clearly and concisely — judges watch many videos
- Don't show any credentials, API keys, or .env files

---

### 4. Upload Video to YouTube
**Time:** 5 minutes

1. Go to https://studio.youtube.com
2. Upload the recorded video
3. Title: `HealthPulse AI — Healthcare Performance Intelligence (Agents Assemble Hackathon)`
4. Description:
   ```
   HealthPulse AI is an MCP server and dashboard that provides healthcare performance
   intelligence across 5,400+ US hospitals using real CMS data, synthetic FHIR patients,
   and CDC Social Vulnerability Index.

   11 MCP tools: quality monitoring, care gap detection, equity analysis,
   facility benchmarking, executive briefing, state ranking, cross-cutting
   multi-factor analysis, patient risk profiling, cohort analysis,
   patient experience, and cost efficiency.

   306 tests. 233K+ rows real data. 100 synthetic FHIR patients.
   Conversational AI chat. PDF export. Deployed on Prompt Opinion, Railway, and Vercel.

   Built for the Agents Assemble Healthcare AI Hackathon on Prompt Opinion.

   GitHub: https://github.com/sgharlow/health-pulse
   MCP Server: https://health-pulse-mcp-production.up.railway.app/mcp
   Dashboard: https://web-umber-alpha-41.vercel.app
   ```
5. Visibility: **Public** or **Unlisted** (both work for Devpost)
6. Copy the YouTube URL

---

### 5. Capture Screenshots
**Time:** 10 minutes
**Why:** Recommended for Devpost submission — makes the project page look professional.

Capture these screenshots and save to `health-pulse/assets/`:

1. **Prompt Opinion Chat** — showing HealthPulse AI agent responding to a quality query with tool call visible
2. **Cross-Cutting Analysis** — showing multi-concern facility results
3. **Equity Analysis** — showing real SVI data with poverty/uninsured rates
4. **Patient Experience** — showing HCAHPS dimensional analysis
5. **Cost Efficiency** — showing spending-quality scatter plot
6. **Dashboard Hub** — showing KPI cards and navigation to all modules
7. **Chat Interface** — showing conversational tool routing with Claude
8. **Executive Briefing** — showing AI narrative with PDF export option
9. **Patient Risk Profile** — showing FHIR patient data and risk assessment
10. **Architecture Diagram** — use the text diagram from `assets/architecture.md` or create a visual version

---

### 6. Submit on Devpost
**Time:** 30 minutes
**URL:** https://agents-assemble.devpost.com/

#### Required Fields

| Field | Value |
|-------|-------|
| **Project Name** | HealthPulse AI |
| **Tagline** | Healthcare performance intelligence across 5,400+ US hospitals — 11 MCP tools, real CMS data, synthetic FHIR patients, conversational AI |
| **About** | Copy from `assets/SUBMISSION.md` (the full text) |
| **Built With** | Python, MCP, FastMCP, Domo, Starlette, Next.js, TypeScript, Tailwind CSS, Recharts, Vitest, @anthropic-ai/sdk, @react-pdf/renderer, Railway, Vercel, Synthea |
| **Try It Out** | Prompt Opinion marketplace URL (from step 2) |
| **Demo Video** | YouTube URL (from step 4) |
| **Repository** | https://github.com/sgharlow/health-pulse |
| **Images** | Upload screenshots from step 5 |

#### Submission Text Structure

The text in `assets/SUBMISSION.md` is organized around the 3 judging criteria:

1. **The AI Factor** — 11 MCP tools spanning 6 analytical dimensions, Z-score anomaly detection, cross-cutting multi-factor analysis, FHIR patient drill-down, conversational chat with Claude tool routing, AI narrative briefing with PDF export, HCAHPS patient experience, Medicare cost-quality correlation
2. **Potential Impact** — $26B readmission costs, $500M+ CMS penalties, 100K+ preventable deaths. Found 94/222 FL hospitals with compounding concerns. Patient experience scores connecting to readmission rates. Cost-quality analysis proving efficiency and quality coexist.
3. **Feasibility** — Zero PHI (all CMS/CDC public + Synthea synthetic), Domo enterprise platform, SHARP/MCP/FHIR open standards, 306 tests, production deployment on Railway + Vercel, unified dashboard hub with 3 access modalities

---

## Post-Submission (Optional Enhancements)

These can be added after initial submission (Devpost allows edits until deadline):

| Enhancement | Impact | Time |
|-------------|--------|------|
| Add real EHR FHIR endpoint integration | High — moves from synthetic to live patient data | 2-3 days |
| Add predictive risk scoring model | High — forward-looking analytics | 2-3 days |
| Add geographic map visualization | Medium — visual impact for judges | 1 day |

---

## Deployment URLs

| Service | URL |
|---------|-----|
| **MCP Server (Railway)** | https://health-pulse-mcp-production.up.railway.app/mcp |
| **Dashboard (Vercel)** | https://web-umber-alpha-41.vercel.app |
| **GitHub** | https://github.com/sgharlow/health-pulse |
| **Prompt Opinion** | https://app.promptopinion.ai (HealthPulse AI agent) |

---

## Project Stats

| Metric | Value |
|--------|-------|
| MCP Tools | 11 |
| MCP Resources | 6 (4 static + 2 URI templates) |
| Domo Datasets | 7 (233K+ rows) |
| Synthetic FHIR Patients | 100 (1,002 resources) |
| CMS Hospitals | 5,426 |
| Tests | 306 (243 MCP + 63 web Vitest) |
| Dashboard Pages | 7 |
| API Routes | 6 |
| Chat Interface | Claude-powered conversational tool routing |
| AI Briefing | Narrative generation with PDF export |
| Commits | 30 |
