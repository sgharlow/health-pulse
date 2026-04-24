# HealthPulse AI — Submission Index

> **Hackathon:** Agents Assemble (Prompt Opinion, $25,000) · **Deadline:** May 11, 2026

This root-level file is a one-page pointer for judges. Everything you need is linked below. Detailed narrative lives in [`assets/SUBMISSION.md`](./assets/SUBMISSION.md).

## At a Glance

- **What it is:** 11-tool MCP server + Next.js dashboard surfacing 233K+ rows of real CMS hospital quality data across 5,400+ facilities, plus a 100-patient synthetic FHIR layer.
- **Why it matters:** Healthcare quality data is published but effectively inaccessible. HealthPulse exposes it as tools any AI agent can call in natural language — no SQL, no dashboard login, no PhD.
- **What's live:** Dashboard + MCP server + chat interface + AI narrative briefing, all in production.

## Live Deployments

| | URL |
|---|---|
| **Devpost project** | _TODO: paste the devpost.com/software/... URL once visible to Steve_ |
| **Demo Video (2:18)** | https://youtu.be/40haMLuDOIk |
| **Dashboard** | https://web-umber-alpha-41.vercel.app |
| **MCP Server** | https://health-pulse-mcp-production.up.railway.app/mcp |
| **GitHub** | https://github.com/sgharlow/health-pulse |

## Submission Material

| Deliverable | File |
|---|---|
| Detailed submission narrative (Summary, AI Factor, Impact, Feasibility) | [`assets/SUBMISSION.md`](./assets/SUBMISSION.md) |
| Devpost-formatted submission | [`docs/devpost-submission.md`](./docs/devpost-submission.md) |
| Demo video script (3 minutes) | [`assets/VIDEO-SCRIPT.md`](./assets/VIDEO-SCRIPT.md) |
| Prompt Opinion demo guide | [`assets/PROMPT-OPINION-DEMO-GUIDE.md`](./assets/PROMPT-OPINION-DEMO-GUIDE.md) |
| Architecture (server + dashboard + data flow) | [`assets/architecture.md`](./assets/architecture.md) |
| Demo screenshots (10 numbered PNGs) | [`assets/screenshots/`](./assets/screenshots/) |
| Remaining manual steps before submission | [`docs/REMAINING-STEPS.md`](./docs/REMAINING-STEPS.md) |

## Tests

- **313 automated tests**, all passing.
- 250 MCP server (pytest, `cd mcp-server && pytest`)
- 63 web dashboard (vitest, `cd web && npm test`)
- CI workflow: [`.github/workflows/test.yml`](./.github/workflows/test.yml)

## Local Run

See the [Quick Start section of the README](./README.md#quick-start). Requires Python 3.11+, Domo developer credentials, and Node 20+ for the dashboard.

## License

MIT — see [`LICENSE`](./LICENSE).
