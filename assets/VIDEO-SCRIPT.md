# HealthPulse AI — Demo Video Script (3 Minutes)

> For use with NotebookLM audio generation.
> Each section includes the screenshot to display and the narration text.
> Total runtime: approximately 2:55.

---

## [0:00 - 0:20] Opening — The Hub

**Show:** `01-hub-landing.png`

**Narration:**

Every year, Medicare readmission penalties cost US hospitals over 500 million dollars. Quality officers spend hours buried in spreadsheets trying to spot problems before they become crises. HealthPulse AI changes that.

This is HealthPulse AI — a healthcare performance intelligence platform built on the Model Context Protocol. Eleven MCP tools, 233,000 rows of real CMS data, 5,426 hospitals, 100 synthetic FHIR patients, and three ways to access it: a visual dashboard, a conversational chat interface, and the Prompt Opinion marketplace.

---

## [0:20 - 0:45] The Dashboard — National Overview

**Show:** `02-dashboard-all-states.png`

**Narration:**

Let's start with what we're monitoring. Across all 5,426 US hospitals, the national average star rating is 3.08 out of 5. We've flagged 450 quality measures rated worse than national benchmarks, out of nearly 30,000 measures tracked.

The star distribution tells an important story. Most hospitals cluster at 3 stars, but look at this — the red bar on the left shows hundreds of hospitals stuck at 1 or 2 stars. And the chart on the right shows which states carry the most low-rated facilities: California, New York, Florida, Illinois, and Texas.

**Show:** `03-dashboard-california.png`

This is California filtered. We can drill into any state and see its specific quality profile instantly.

---

## [0:45 - 1:05] Facilities and Comparison

**Show:** `04-facilities-table.png`

**Narration:**

The facilities view lets you search and sort all 5,426 hospitals. Every facility shows its state, CMS star rating, and hospital type — all pulled from real CMS Hospital General Information data.

**Show:** `05-compare-facilities.png`

And the comparison tool lets you benchmark any two hospitals side by side. Select UCSF Medical Center against Cleveland Clinic, and you get quality measures, readmission rates, and performance data in a structured, AI-readable format.

---

## [1:05 - 1:30] Health Equity — The Disparity No Dashboard Shows

**Show:** `06-equity-analysis.png`

**Narration:**

This is where it gets powerful. The equity analysis correlates hospital quality with the CDC Social Vulnerability Index at the county level. Out of 5,223 facilities with SVI data, 1,708 serve high-vulnerability communities.

And look at this number: a 0.77-star rating disparity. Hospitals in low-vulnerability areas average 3.53 stars. Hospitals in high-vulnerability areas average just 2.75. That is a measurable, systemic gap that affects millions of patients — and no traditional dashboard surfaces it. HealthPulse AI computes it with a single tool call.

---

## [1:30 - 1:55] Executive Briefing — AI-Powered Intelligence

**Show:** `07-briefing-executive.png`

**Narration:**

The executive briefing page aggregates everything into a state-level intelligence report. Here's California: 378 hospitals, a 3.01 average star rating, 253 care gaps, and 30 high-risk counties. The star distribution, the worst-performing facilities, the readmission analysis — all generated from real CMS data in seconds.

**Show:** `10-briefing-ai-narrative.png`

And with one click, Claude generates a narrative executive summary. Key findings, anomalies and alerts, equity insights, and recommended actions — all grounded in the data we just saw. This is board-ready healthcare intelligence. And you can download the entire briefing as a PDF.

---

## [1:55 - 2:35] Conversational AI — Ask Anything

**Show:** `08-chat-interface.png`

**Narration:**

But the real differentiator is conversational access. The chat interface connects directly to all 11 MCP tools through Claude. You don't need to know which tool to use or what parameters to set. Just ask a question in plain English.

**Show:** `09-chat-quality-response.png`

Here I asked: "What are the worst quality hospitals in California?" Claude automatically selected the right tool, queried the real CMS data, and returned a structured answer. Kaweah Health Medical Center and Adventist Health facilities topped the list with multiple quality flags. UCI Health Los Alamitos showed 48% higher hip and knee readmissions than expected. Providence St. Mary and Oroville Hospital showed 43% excess readmission rates.

These aren't synthetic examples. These are real CMS findings from real hospital data.

---

## [2:35 - 2:55] Closing — Why This Matters

**Show:** `01-hub-landing.png`

**Narration:**

HealthPulse AI is 11 MCP tools covering quality monitoring, care gap detection, equity analysis, patient experience, cost efficiency, facility benchmarking, state rankings, cross-cutting risk analysis, executive briefings, and patient-level FHIR drill-down.

233,000 rows of real CMS data. 100 synthetic FHIR patients with SHARP context propagation. A conversational chat interface. AI narrative generation with PDF export. 306 automated tests. Deployed on Railway and Vercel, published on the Prompt Opinion marketplace.

This is healthcare performance intelligence — built for AI agents, powered by real data, ready for production.

HealthPulse AI. Built for the Agents Assemble Healthcare AI Hackathon.

---

## Screenshot Reference

| Timestamp | Screenshot | Content |
|-----------|-----------|---------|
| 0:00 | `01-hub-landing.png` | Three-card hub with 11 MCP Tools stats |
| 0:20 | `02-dashboard-all-states.png` | National KPIs, star distribution, low-rated states chart |
| 0:40 | `03-dashboard-california.png` | California-filtered dashboard |
| 0:45 | `04-facilities-table.png` | Searchable facility table, 5,426 hospitals |
| 0:55 | `05-compare-facilities.png` | Side-by-side facility comparison |
| 1:05 | `06-equity-analysis.png` | SVI analysis, 0.77-star disparity, high-SVI facilities |
| 1:30 | `07-briefing-executive.png` | CA briefing: 378 facilities, star distribution, worst performers |
| 1:45 | `10-briefing-ai-narrative.png` | Claude AI narrative with findings and recommendations |
| 1:55 | `08-chat-interface.png` | Chat welcome with suggested queries |
| 2:05 | `09-chat-quality-response.png` | Real response: worst CA hospitals with specific data |
| 2:35 | `01-hub-landing.png` | Return to hub for closing |

## Production Notes

- Total narration: approximately 2 minutes 55 seconds at natural speaking pace
- All data shown is real CMS data, not mocked or fabricated
- Key numbers to emphasize: 5,426 hospitals, 450 quality flags, 0.77 star disparity, 48% excess readmissions, 313 tests, 11 tools
- Tone: professional, data-driven, understated confidence — let the numbers speak
- For NotebookLM: paste this entire script as source material and request a "3-minute product demo narration in a professional, documentary tone"
