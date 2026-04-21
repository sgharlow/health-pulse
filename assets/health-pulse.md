# 

## 1. Health Pulse — Record Demo + Submit on Devpost

**Priority:** HIGH
**Deadline:** May 11, 2026, 11:00 PM EDT (25 days)
**Est. Time:** 2-3 hours (including retakes)
**Project:** `CascadeProjects/health-pulse`

### Step 1: Verify Prompt Opinion Publishing (5 min)

1. Go to https://app.promptopinion.ai
2. Navigate to **Marketplace Studio** > **MCP Servers**
3. Confirm **HealthPulse AI** shows with **Published** toggle **ON**
4. Copy the marketplace URL (needed for Devpost)
5. Navigate to **Launchpad** > select **HealthPulse AI** agent
6. Send test query: `"Check for quality anomalies in Texas hospitals"`
7. Verify the agent responds with real data (tool call visible, anomalies listed)

### Step 2: Record Demo Video — Under 3 Minutes (1-2 hours)

**Setup:**

- Screen recording: OBS, Loom, or Windows Game Bar (`Win+G`)
- Browser to Prompt Opinion at 1920x1080
- Enable "Show Tool calls" toggle in chat interface
- Close other tabs/notifications

**Script (copy-paste these queries in order):**

| Timestamp | Action                                                                                                                                                                                                                                                                                                                                                                 |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0:00-0:15 | **Intro:** "HealthPulse AI is a healthcare performance intelligence platform with 11 MCP tools that monitors quality metrics, detects anomalies, identifies equity disparities, analyzes patient experience, benchmarks cost efficiency, and profiles patient risk across 5,400 US hospitals — powered by real CMS data, synthetic FHIR patients, and Domo analytics." |
| 0:15-0:50 | **Type:** `Show me quality anomalies in California hospitals` — highlight Z-scores and critical findings                                                                                                                                                                                                                                                               |
| 0:50-1:20 | **Type:** `Find facilities in Florida with multiple compounding concerns` — highlight "94 of 222 Florida hospitals have 2+ simultaneous concerns"                                                                                                                                                                                                                      |
| 1:20-1:45 | **Type:** `How do patients rate hospital care in New York?` — highlight HCAHPS dimensions                                                                                                                                                                                                                                                                              |
| 1:45-2:10 | **Type:** `Check for equity disparities and cost efficiency in Texas hospitals` — highlight SVI data                                                                                                                                                                                                                                                                   |
| 2:10-2:30 | **Type:** `Show me the risk profile for patient Aaron697` — highlight FHIR patient data                                                                                                                                                                                                                                                                                |
| 2:30-2:50 | **Type:** `Compare UCSF Medical Center (050454) with NYU Langone (330214) and show me the worst-performing states` — highlight side-by-side                                                                                                                                                                                                                            |
| 2:50-3:00 | **Closing:** "HealthPulse AI — 11 MCP tools, 233,000 rows of real CMS data, 100 synthetic FHIR patients, conversational AI chat, and PDF export — deployed on Prompt Opinion, Railway, and Vercel."                                                                                                                                                                    |

**Tips:**

- Keep queries short — the agent needs time to respond
- Speed up slow responses slightly in editing
- Don't show credentials, API keys, or .env files

### Step 3: Upload Video to YouTube (5 min)

1. Go to https://studio.youtube.com

2. Upload the recorded video

3. **Title:** `HealthPulse AI — Healthcare Performance Intelligence (Agents Assemble Hackathon)`

4. **Description:**
   
   ```
   HealthPulse AI is an MCP server and dashboard that provides healthcare
   performance intelligence across 5,400+ US hospitals using real CMS data,
   synthetic FHIR patients, and CDC Social Vulnerability Index.
   
   11 MCP tools. 313 tests. 233K+ rows real data. 100 synthetic FHIR patients.
   Conversational AI chat. PDF export.
   
   GitHub: https://github.com/sgharlow/health-pulse
   MCP Server: https://health-pulse-mcp-production.up.railway.app/mcp
   Dashboard: https://web-umber-alpha-41.vercel.app
   ```

5. Visibility: **Public** or **Unlisted**

6. Copy the YouTube URL

### Step 4: Capture Screenshots (10 min)

Save to `health-pulse/assets/`:

1. Prompt Opinion Chat — quality query with tool call visible
2. Cross-Cutting Analysis — multi-concern facilities
3. Equity Analysis — real SVI data
4. Dashboard Hub — KPI cards and navigation
5. Chat Interface — conversational tool routing
6. Executive Briefing — AI narrative with PDF export

### Step 5: Submit on Devpost (30 min)

URL: https://agents-assemble.devpost.com/

| Field        | Value                                                                                                                                    |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Project Name | HealthPulse AI                                                                                                                           |
| Tagline      | Healthcare performance intelligence across 5,400+ US hospitals — 11 MCP tools, real CMS data, synthetic FHIR patients, conversational AI |
| About        | Copy from `health-pulse/docs/devpost-submission.md`                                                                                      |
| Built With   | Python, MCP, FastMCP, Domo, Next.js, TypeScript, Tailwind CSS, Recharts, Vitest, Railway, Vercel, Synthea                                |
| Try It Out   | Prompt Opinion marketplace URL (from Step 1)                                                                                             |
| Demo Video   | https://youtu.be/40haMLuDOIk                                                                                                             |
| Repository   | https://github.com/sgharlow/health-pulse                                                                                                 |
| Images       | Upload screenshots from Step 4                                                                                                           |

---

## 
