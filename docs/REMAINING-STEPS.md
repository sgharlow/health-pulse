# HealthPulse AI — Remaining Steps to Submission

> Last updated: 2026-03-15
> Deadline: May 11, 2026, 11:00 PM EDT (57 days remaining)
> All code/data/deployment work is complete. Only manual steps remain.

---

## Pre-Submission Checklist

### 1. Disable Vercel Deployment Protection
**Time:** 2 minutes
**Why:** The dashboard returns 401 for public visitors due to Vercel's Deployment Protection.

1. Go to https://vercel.com
2. Open project **"web"** (steves-projects-a71becf4)
3. Go to **Settings** > **Deployment Protection**
4. Set production protection to **Disabled** (or "Only Preview Deployments")
5. Save
6. Verify by visiting: https://web-umber-alpha-41.vercel.app/dashboard

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
"HealthPulse AI is a healthcare performance intelligence agent that monitors quality metrics, detects anomalies, identifies equity disparities, and benchmarks facilities across 5,400 US hospitals — powered by real CMS data through Domo analytics."

**[0:15-0:50] Quality Anomaly Detection**
Type: `Show me quality anomalies in California hospitals`
- Wait for response — agent calls `quality_monitor`
- Briefly highlight: number of anomalies, a critical finding (Z-score, facility name)

**[0:50-1:30] Cross-Cutting Multi-Factor Analysis**
Type: `Find facilities in Florida with multiple compounding concerns`
- Wait for response — agent calls `cross_cutting_analysis`
- Highlight: "94 of 222 Florida hospitals have 2+ simultaneous concerns"
- Point out a facility with quality + readmission + equity issues together

**[1:30-2:00] Health Equity Analysis**
Type: `Check for equity disparities among New York hospitals`
- Wait for response — agent calls `equity_detector`
- Highlight: real CDC SVI data — BronxCare at SVI 0.997, 38.6% poverty, 7.6% uninsured

**[2:00-2:30] Facility Benchmark**
Type: `Compare UCSF Medical Center (050454) with NYU Langone (330214)`
- Wait for response — agent calls `facility_benchmark`
- Highlight: side-by-side quality measures, star ratings

**[2:30-2:50] State Performance Ranking**
Type: `Which states have the worst overall healthcare performance?`
- Wait for response — agent calls `state_ranking`
- Highlight: Mississippi at composite 24.9, comparison with top states

**[2:50-3:00] Closing**
"HealthPulse AI — 7 MCP tools, 236,000 rows of real CMS data, CDC Social Vulnerability Index, SHARP healthcare context, deployed on the Prompt Opinion platform."

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
   HealthPulse AI is an MCP server that provides healthcare performance intelligence
   across 5,400+ US hospitals using real CMS data and CDC Social Vulnerability Index.

   7 MCP tools: quality monitoring, care gap detection, equity analysis,
   facility benchmarking, executive briefing, state ranking, and cross-cutting
   multi-factor analysis.

   Built for the Agents Assemble Healthcare AI Hackathon on Prompt Opinion.

   GitHub: https://github.com/sgharlow/health-pulse
   MCP Server: https://health-pulse-mcp-production.up.railway.app/mcp
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
4. **Dashboard Overview** — showing KPI cards and Recharts bar charts
5. **Dashboard Briefing** — showing the executive briefing page
6. **Architecture Diagram** — use the text diagram from `assets/architecture.md` or create a visual version

---

### 6. Submit on Devpost
**Time:** 30 minutes
**URL:** https://agents-assemble.devpost.com/

#### Required Fields

| Field | Value |
|-------|-------|
| **Project Name** | HealthPulse AI |
| **Tagline** | Healthcare performance intelligence across 5,400+ US hospitals — powered by real CMS data and Domo analytics |
| **About** | Copy from `assets/SUBMISSION.md` (the full text) |
| **Built With** | Python, MCP, FastMCP, Domo, Starlette, Next.js, TypeScript, Tailwind CSS, Recharts, Railway, Vercel |
| **Try It Out** | Prompt Opinion marketplace URL (from step 2) |
| **Demo Video** | YouTube URL (from step 4) |
| **Repository** | https://github.com/sgharlow/health-pulse |
| **Images** | Upload screenshots from step 5 |

#### Submission Text Structure

The text in `assets/SUBMISSION.md` is organized around the 3 judging criteria:

1. **The AI Factor** — Z-score anomaly detection, cross-cutting multi-factor analysis, clinical context generation, state composite ranking
2. **Potential Impact** — $26B readmission costs, $500M+ CMS penalties, 100K+ preventable deaths. Found 94/222 FL hospitals with compounding concerns. Mississippi at composite 24.9/100.
3. **Feasibility** — Zero PHI (all CMS/CDC public data), Domo enterprise platform, SHARP/MCP open standards, 113 tests, production deployment

---

## Post-Submission (Optional Enhancements)

These can be added after initial submission (Devpost allows edits until deadline):

| Enhancement | Impact | Time |
|-------------|--------|------|
| Add FHIR patient drill-down (Phase 2) | High — completes the SHARP story | 2-3 days |
| Add Claude AI narrative to dashboard briefing page | Medium — strengthens AI Factor | 2-3 hours |
| Add HCAHPS patient experience tool | Medium — uses loaded but unused data | 1 day |
| Add cost efficiency tool | Low — uses loaded but unused data | 1 day |
| Add web-side tests with Vitest | Medium — shows production quality | 2-3 hours |
| Add MCP tool result caching | Low — performance optimization | 1-2 hours |

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
| MCP Tools | 7 |
| MCP Resources | 3 |
| Domo Datasets | 7 (236,749 rows) |
| CMS Hospitals | 5,426 |
| CDC SVI Counties | 3,144 |
| Tests | 113 passing |
| Commits | 23 |
| Source Files | 51 (38 Python + 13 TypeScript) |
| Dashboard Pages | 7 |
| API Routes | 4 |
