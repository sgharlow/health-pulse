# Live Investigation — Prompt for Claude Code (HealthPulse MCP)

This is the prompt you paste into a Claude Code session once the
`health-pulse` MCP server is attached. The agent drives the 11 MCP tools
exposed by the Railway server against real CMS / CDC data.

Unlike the dashboard walkthrough (which is already real — Playwright
against live Vercel + live Domo + live Claude), this adds a *second*
authenticity layer: judges watching the live investigation see an
independent Claude Code instance compose the MCP tools directly,
proving the "any agent can use these" claim from the submission.

## Prerequisites

See `docs/guides/live-mcp-demo-setup.md` for the full setup.

**Blocker**: the local `mcp-server/.env` HP_API_KEY is empty, and the
canonical value is only on Railway. Resolve per recording-health-pulse.md §1G
before running this prompt.

## The prompt (paste into Claude Code)

> You have access to the HealthPulse AI MCP server with 11 forensic tools
> for US hospital quality data. The tools cover quality anomaly detection,
> care-gap identification, health equity analysis (correlated with CDC
> Social Vulnerability Index), facility benchmarking, executive briefing
> generation, state ranking, cross-cutting risk analysis, patient-level
> FHIR risk profiling, cohort analysis, HCAHPS patient experience scoring,
> and Medicare cost-efficiency analysis.
>
> Run an investigation that exercises the tool surface:
>
> 1. **quality_monitor** on California — surface the top quality anomalies.
> 2. **equity_detector** nationwide — characterize the high-vs-low SVI
>    rating gap. Cite the specific disparity number.
> 3. **facility_benchmark** — compare UCSF Medical Center (050454) with
>    Cleveland Clinic (360180) across their shared measures.
> 4. **cross_cutting_analysis** on Florida — find facilities with 2+
>    compounding risk factors.
> 5. **executive_briefing** on California — generate the state briefing.
> 6. **state_ranking** — rank states by low-rated facility count.
> 7. (If patient tools are exposed) **patient_risk_profile** on any
>    FHIR patient ID available.
>
> Narrate what each tool returned. Where a finding is surprising, explain
> why. At the end, summarize what distinguishes HealthPulse from a
> threshold-alert system (z-score vs threshold, multi-dimensional risk
> compounding, equity as a first-class dimension). This is being recorded.

## What to expect

- **~5–8 minutes** of tool calls
- **11 MCP tools** advertised; most investigations touch 6–8 of them
- Real numbers: **5,426 facilities, 233K+ rows, 100 synthetic FHIR patients**
- Claude's wording will vary run-to-run; that's expected

## After the recording

The investigation does not write files locally — it just produces chat
output. Preserve the take by saving the terminal transcript.

Reset for next take:

```bash
# Nothing to clean — the Railway MCP is stateless per request
```
