# HealthPulse AI — Demo Video Script (3 Minutes)

> For use with NotebookLM audio generation.
> **Emphasis: MCP server is the product.** The narration leads with three
> MCP-style tool calls and the AI briefing, then tours the dashboard as
> the secondary "human visualization layer."
> Total runtime: approximately 2:55.

---

## [0:00 - 0:15] Opening — Eleven Tools, One Protocol

**Show:** `01-hub-landing.png`

**Narration:**

Every year, Medicare readmission penalties cost US hospitals over 500 million dollars. HealthPulse AI gives quality officers, payers, and AI agents a different primitive: a Model Context Protocol server exposing eleven healthcare intelligence tools. Any MCP client — Claude Desktop, Prompt Opinion, the Anthropic API, a custom agent — gets the same tools. 233,000 rows of real CMS data. 5,426 hospitals. 100 synthetic FHIR patients. Let me show you the tool layer first.

---

## [0:15 - 0:45] MCP Tool Call #1 — Quality Anomaly Detection

**Show:** `08-chat-interface.png` → `09-chat-quality-response.png`

**Narration:**

The conversational interface routes natural language questions to MCP-style tools. First question: "Show me quality anomalies in California hospitals." The agent invokes the `get_quality_data` tool — the web-side mirror of the MCP server's `quality_monitor`. Response includes facility-level Z-scores and specific hospitals three or more standard deviations from their peers. Kaweah Health. Adventist Health. UCI Health Los Alamitos — 48 percent higher hip and knee readmissions than expected. Statistical pattern detection, not a chart query.

---

## [0:45 - 1:15] MCP Tool Call #2 — Health Equity Disparity

**Show:** Chat response for equity query (captured live during recording)

**Narration:**

Second query: "What's the equity disparity in Texas hospitals?" The `get_equity_analysis` tool correlates hospital quality against the CDC Social Vulnerability Index at the county level. Nationally, a 0.77-star gap between hospitals serving high-vulnerability communities and those in affluent areas. 1,708 facilities in the high-SVI tier, millions of patients affected. One tool call, a systemic disparity surfaced.

---

## [1:15 - 1:40] MCP Tool Call #3 — Facility Benchmarking

**Show:** Chat response for compare query

**Narration:**

Third query: "Compare UCSF Medical Center and Cleveland Clinic." The `compare_facilities` tool — equivalent to the MCP server's `facility_benchmark` — returns side-by-side quality measures, readmission rates, and safety scores in a structured, LLM-readable format. These three are a slice of the eleven the MCP server exposes. The full set — quality monitor, care gap finder, equity detector, facility benchmark, executive briefing, state ranking, cross-cutting analysis, patient risk profile, patient cohort analysis, patient experience, cost efficiency — lives at our Railway MCP endpoint and on the Prompt Opinion marketplace.

---

## [1:40 - 2:05] MCP Tool Call #4 — AI Executive Briefing

**Show:** `07-briefing-executive.png` → `10-briefing-ai-narrative.png`

**Narration:**

The fourth tool — `get_ai_briefing` — aggregates state-level data into a board-ready narrative. Here's California: 378 hospitals, 3.01 average stars, 253 care gaps, 30 high-risk counties. One click, Claude composes key findings, anomalies, equity insights, and recommended actions. PDF export ships built in. This is the final MCP tool in the demo; everything after this is presentation.

---

## [2:05 - 2:45] Dashboard — Same Tools, Visualized

**Show:** `02-dashboard-all-states.png` → `03-dashboard-california.png` → `04-facilities-table.png` → `05-compare-facilities.png` → `06-equity-analysis.png`

**Narration:**

Built on top of the MCP server, a Next.js dashboard renders the same tool outputs for human consumption. The national view: 5,426 hospitals, a 3.08 average star rating, and the low-performing-state ranking. Filter to California and the same lens focuses. The facilities table lets you search and sort every hospital — try UCSF. The compare page benchmarks any two facilities side by side — UCSF against Cleveland Clinic, quality measures aligned. And the equity page visualizes that 0.77-star gap the tool computes — one tool call, one chart. No matter the surface — chat, dashboard, MCP client — the intelligence comes from the same tool layer.

---

## [2:45 - 2:55] Closing

**Show:** `01-hub-landing.png`

**Narration:**

HealthPulse AI: eleven MCP tools, 233,000 rows of real CMS data, 100 synthetic FHIR patients, SHARP context propagation, 313 automated tests. MCP server is the product; the dashboard is the human interface. Deployed on Railway, published on Prompt Opinion. Built for the Agents Assemble Healthcare AI Hackathon.

---

## Screenshot Reference

| Timestamp | Screenshot | Content |
|-----------|-----------|---------|
| 0:00 | `01-hub-landing.png` | Three-card hub with 11 MCP Tools headline |
| 0:15 | `08-chat-interface.png` | Chat welcome with suggested queries |
| 0:25 | `09-chat-quality-response.png` | `get_quality_data` tool call + response |
| 0:45 | *(captured live during recording)* | `get_equity_analysis` response |
| 1:15 | *(captured live during recording)* | `compare_facilities` response |
| 1:40 | `07-briefing-executive.png` | Briefing executive view |
| 1:50 | `10-briefing-ai-narrative.png` | Claude AI narrative + PDF export |
| 2:05 | `02-dashboard-all-states.png` | National KPIs dashboard |
| 2:15 | `03-dashboard-california.png` | Dashboard filtered to CA |
| 2:20 | `04-facilities-table.png` | Facilities table with UCSF search |
| 2:28 | `05-compare-facilities.png` | Side-by-side comparison |
| 2:38 | `06-equity-analysis.png` | SVI equity visualization |
| 2:45 | `01-hub-landing.png` | Return to hub |

## Production Notes

- Total narration: approximately 2 minutes 55 seconds at natural speaking pace
- **Emphasis ratio:** MCP-layer story consumes 0:15–2:05 (~110 seconds); dashboard tour 2:05–2:45 (~40 seconds). Roughly 3:1 MCP-to-web.
- All data shown is real CMS data, not mocked or fabricated
- Key numbers to emphasize: 11 MCP tools, 5,426 hospitals, 0.77 star equity disparity, 48% excess readmissions, 233K rows, 313 tests
- Tone: professional, data-driven, understated confidence — MCP is a *product primitive* here, not a buzzword
- For NotebookLM: paste this entire script as source material and request a "3-minute product demo narration in a professional, documentary tone, emphasizing that the MCP server is the primary product and the dashboard is built on top of it"
- **For the live Prompt Opinion MCP demo** (all 11 tools, no web UI), see `PROMPT-OPINION-DEMO-GUIDE.md`
