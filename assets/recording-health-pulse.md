# Hackathon Recording Readiness

## TL;DR

| Hackathon              | Project      | Deadline   | Days Left | Code Done       | Repo Public?   | Demo Recordable Today?                     |
| ---------------------- | ------------ | ---------- | --------- | --------------- | -------------- | ------------------------------------------ |
| Agents Assemble ($25K) | Health Pulse | 2026-05-11 | 23        | YES (313 tests) | Already public | YES — every script number matches live API |

---

## 1. HEALTH PULSE — Agents Assemble

### 1A. Submission Metadata (paste-ready)

| Field                | Value                                                  |
| -------------------- | ------------------------------------------------------ |
| Name                 | HealthPulse AI                                         |
| Repo                 | https://github.com/sgharlow/health-pulse               |
| Demo URL (dashboard) | https://web-umber-alpha-41.vercel.app                  |
| MCP endpoint         | https://health-pulse-mcp-production.up.railway.app/mcp |
| License              | MIT                                                    |
| Team                 | Steve Harlow (solo)                                    |

**Tagline:** An 11-tool MCP server plus Next.js dashboard that turns 233,000+ rows of public CMS hospital quality data into AI-actionable healthcare intelligence any agent can call in plain English.

**Description (~150 words):**

> HealthPulse AI gives any AI agent eleven Model Context Protocol (MCP) tools backed by 233,000+ rows of real CMS hospital quality data covering 5,400+ US facilities and a 100-patient synthetic FHIR layer. The tools span quality anomaly detection (Z-score across all hospitals), care-gap identification, health equity analysis correlating outcomes with the CDC Social Vulnerability Index, facility benchmarking, executive briefing generation, state ranking, six-dimension cross-cutting risk analysis, patient-level FHIR risk profiling, cohort analysis, HCAHPS patient experience scoring, and Medicare cost-efficiency analysis. A Next.js dashboard adds seven visual pages, an Anthropic-powered chat interface that auto-routes natural language to the right tool, AI narrative briefings, and PDF export. The system is production-deployed on Railway (MCP server) and Vercel (dashboard), backed by 313 automated tests, registered on the Prompt Opinion marketplace, and uses zero PHI — only public CMS/CDC data plus synthetic Synthea patients.

**Tech stack:** Python 3.11 + FastMCP + Starlette + uvicorn (Streamable HTTP); Next.js 16 + React 19.2 + TS + Tailwind 4 + Recharts + `@react-pdf/renderer`; Anthropic SDK 0.78 (`claude-sonnet-4-20250514`); Domo (REST + SQL endpoint, 7 datasets, OAuth2 client credentials); FHIR R4 / Synthea; SHARP-on-MCP (X-FHIR-Server-URL / X-Patient-ID / X-FHIR-Access-Token); pytest + Vitest; Docker on Railway, Vercel for dashboard, GitHub Actions CI.

**Multi-agent angle:** HealthPulse exposes 11 discoverable tools any LLM agent can compose — `quality_monitor` → `equity_detector` → `patient_risk_profile` in one conversation. Dashboard chat demonstrates Claude tool-routing; SHARP headers carry FHIR patient context across calls (population → patient workflow). Listed on Prompt Opinion marketplace.

**Pre-existing source-of-truth files:** `SUBMISSION.md` (root), `assets/SUBMISSION.md`, `docs/devpost-submission.md`.

### 1B. Branding Brief

**Visual identity:** Deep teal `#0E7C7B` primary, coral `#FF6B6B` anomaly accent, sand `#F5F1E8` backdrop, charcoal `#1F2933` type. Mood: clinical, data-confident, hopeful — public-health agency rebrand, not hospital-sterile. Metaphor: EKG waveform crossed with a network graph; each beat = a hospital, the line = the population signal.

**Logo prompt (Midjourney / Imagine / Ideogram):**

> A modern, minimal logo for "HealthPulse AI" — a healthcare analytics platform. Wordmark in a clean geometric sans-serif (Inter or Space Grotesk weight 600). Adjacent symbol: a single horizontal EKG/pulse waveform that morphs mid-stroke into three connected circular nodes, suggesting both a heartbeat and a network of hospitals. Primary color deep teal (#0E7C7B), accent coral (#FF6B6B) on the rightmost node, charcoal type. Flat vector, no gradients, no glow, no AI-generic chrome. Square and horizontal lockups. Background transparent. Should read clearly at favicon size and on a dark slide.

**Architecture diagram prompt:**

> An isometric system diagram for "HealthPulse AI" with three horizontal layers stacked top to bottom on a soft sand background. TOP layer "Access" shows three rounded cards side-by-side: "Prompt Opinion Marketplace" (agent icon), "Next.js Dashboard" (browser icon with 7 small page tiles), and "Chat Interface" (speech bubble with Claude logo). MIDDLE layer "HealthPulse MCP Server (Railway)" is a wide teal rounded rectangle containing two small badges (API-Key Auth, SHARP Middleware) and a 4x3 grid of tool tiles labeled with the 11 tool names grouped into Quality+Safety, Equity+Experience, Benchmarking+Ranking, Patient-Level (FHIR), Executive. Streamable HTTP arrows with a small "SHARP headers" tag flow from top to middle. BOTTOM layer splits into two: "Domo Platform" cylinder containing 7 dataset chips totaling 233K rows, and "Synthea FHIR Layer" containing a patient icon with "100 patients / 1,002 resources." A thin "CMS / CDC Public Data" feeder pipe enters Domo from the side. Color palette: deep teal primary (#0E7C7B), coral accent (#FF6B6B) on alert/anomaly callouts, charcoal labels. Clean line work, generous whitespace, no skeuomorphism.

### 1C. NotebookLM Video Script Source (~430 words)

> **HealthPulse AI — Audio Overview Source**
> 
> **The problem.** Every quarter the Centers for Medicare and Medicaid Services publish quality data on more than five thousand US hospitals — readmission rates, mortality measures, patient experience surveys, safety events. The data is free, public, and de-identified. It is also effectively unusable. To extract a single insight you need SQL, a BI tool, and a statistician. Health systems pay over five hundred million dollars a year in CMS readmission penalties, and the CDC estimates a hundred thousand preventable deaths annually from the very events these datasets already expose. The information exists. The access does not.
> 
> **The solution.** HealthPulse AI is a Model Context Protocol server that gives any AI agent eleven analytics tools backed by two hundred thirty-three thousand rows of real CMS data across fifty-four hundred hospitals, plus a hundred synthetic patients in FHIR format. An agent can call quality_monitor, care_gap_finder, equity_detector, facility_benchmark, executive_briefing, state_ranking, cross_cutting_analysis, patient_risk_profile, patient_cohort_analysis, patient_experience, or cost_efficiency — all by name, all with structured results.
> 
> **How it works.** A Python FastMCP server runs on Railway behind an API key gate. It connects to Domo, where seven curated datasets hold the CMS and CDC Social Vulnerability data. SHARP headers propagate FHIR patient context per request, so the same agent that just looked at California state rankings can drill into a specific patient's risk profile in the next turn. A Next.js dashboard on Vercel surfaces seven visual pages — hub, dashboard, facilities, compare, equity, briefing, and chat — with an Anthropic-powered chat interface that routes natural language to the right MCP tool automatically.
> 
> **Demo highlights.** Run quality_monitor on California and get a hundred ten critical anomalies, three or more standard deviations from peers, that no threshold-based alert would ever catch. Run cross_cutting_analysis on Florida and find that ninety-four of two hundred twenty-two hospitals have two or more compounding risk factors. Generate an executive briefing and export it as a PDF in one click.
> 
> **What's novel.** The MCP server itself does not call an LLM — it returns structured data for the host model to reason over, which kills latency and cost cascades. SHARP-on-MCP support means real EHR integration is an environment-variable change, not a rewrite. The same tools work in Prompt Opinion, in the dashboard, and in any third-party agent.
> 
> **Why it wins.** Production deployed today. Three hundred thirteen automated tests passing. Real public data, zero PHI. Tools any agent can compose. Healthcare AI most teams describe — HealthPulse ships.

### 1D. Demo Recording Infrastructure (verified live)

**Status:** Dashboard video is recordable today against live infrastructure. Every figure in `assets/VIDEO-SCRIPT.md` matches what the live endpoints currently return.

| Component          | Status                                       | Notes                                                                 |
| ------------------ | -------------------------------------------- | --------------------------------------------------------------------- |
| Vercel dashboard   | LIVE (HTTP 200)                              | All 6 API routes returning real Domo data                             |
| Railway MCP server | LIVE                                         | `liveness.sh` GREEN                                                   |
| Domo backend       | LIVE                                         | All 7 dataset IDs + OAuth creds set on Vercel; no mock fallback       |
| Anthropic chat     | LIVE                                         | `claude-sonnet-4-20250514` in `web/src/app/api/chat/route.ts:174-330` |
| AI briefing        | LIVE                                         | ~19 s — pre-warm by clicking once before recording                    |
| Synthea FHIR       | Baked into Railway image (`Dockerfile:9-13`) | Patient tools live on MCP only                                        |
| Demo cost          | <$1                                          | 10–15 Claude calls + 1–2 ai-briefing calls per 5-min demo             |

**Verified figures matching script word-for-word right now:**

- `/api/data` → 5,426 facilities, avg 3.08, 450 flags, 29,765 measures
- `/api/equity` → 0.77 star disparity, 1,708 high-SVI, 5,223 with SVI
- `/api/briefing?state=CA` → 378 facilities, 3.01 avg, 253 care gaps, 30 high-SVI counties
- AI briefing: real Claude narrative referencing 378 facilities and "23% bottom two stars"

**Known facility IDs for the compare scene:** UCSF `050454`, Cleveland Clinic `360180`.

### 1E. Recommended Manufactured Scenario (matches `assets/VIDEO-SCRIPT.md`)

| Step | Action                                                      | URL/data                                            | Env needed                     |
| ---- | ----------------------------------------------------------- | --------------------------------------------------- | ------------------------------ |
| 1    | Hub, show 3 cards                                           | `/`                                                 | none                           |
| 2    | National dashboard, point to 5,426 / 3.08 / 450             | `/dashboard` → `/api/data`                          | DOMO_*, 7 dataset IDs (Vercel) |
| 3    | Filter to CA, state-specific KPIs                           | `/dashboard?state=CA`                               | same                           |
| 4    | Facilities table, search "UCSF"                             | `/facilities`                                       | same                           |
| 5    | Compare UCSF vs Cleveland Clinic (`050454`, `360180`)       | `/compare`                                          | same                           |
| 6    | Equity page — 0.77 disparity, 1,708 high-SVI                | `/equity` → `/api/equity`                           | same                           |
| 7    | Briefing CA — 378 / 3.01 / 253 care gaps                    | `/briefing?state=CA` → `/api/briefing`              | same                           |
| 8    | Click "Generate AI narrative" (PRE-WARM ONCE FIRST)         | `/api/ai-briefing`                                  | + ANTHROPIC_API_KEY            |
| 9    | Click "Download PDF"                                        | `web/src/lib/pdf/download-pdf.ts`                   | none                           |
| 10   | Chat: "What are the worst quality hospitals in California?" | `/chat` → `/api/chat` → Claude → `get_quality_data` | + ANTHROPIC_API_KEY            |
| 11   | Return to hub, closing narration                            | `/`                                                 | none                           |

**Sample chat prompts (paste-ready):**

1. `What are the worst quality hospitals in California?`
2. `Show me equity disparities nationwide`
3. `Compare UCSF Medical Center and Cleveland Clinic` (IDs `050454`, `360180`)
4. `Generate an executive briefing for Florida`
5. `Which states have the most low-rated hospitals?`
6. `Why are readmission rates so high in California?`
7. `What's the star disparity between high and low SVI counties?`

### 1F. Recording Pre-flight Checklist

- [ ] Chrome incognito, 1920×1080, zoom 100%, hide bookmarks bar, close notifications
- [ ] Screen recorder (OBS / Loom / Win+G), mic tested
- [ ] Script open on second monitor
- [ ] Pre-warm Vercel: hit `/`, `/dashboard`, `/equity`, `/briefing?state=CA` ~2 min before recording
- [ ] Pre-generate the AI briefing once so the cached narrative renders fast
- [ ] (For Prompt Opinion video) Verify `HP_API_KEY` parity — see § 1G

### 1G. HP_API_KEY Parity Playbook (manual — Railway CLI not installed)

The audit found that the local `mcp-server/.env` `HP_API_KEY` does NOT authenticate against Railway (returned 401 for `tools/list` with the local key). This blocks the Prompt Opinion marketplace video unless the three values match.

**Three locations must agree:**

1. Local: `health-pulse/mcp-server/.env` → `HP_API_KEY=...`
2. Railway: project env vars dashboard → `HP_API_KEY`
3. Prompt Opinion: marketplace MCP integration secrets → `HP_API_KEY` (whatever name the platform uses for custom headers)

**Recommended sequence (decide canonical value first):**

1. Open `health-pulse/mcp-server/.env` and copy the current `HP_API_KEY=` value (this is your canonical local value per the user's CLAUDE.md "local .env is single source of truth" rule).
2. Open Railway → health-pulse-mcp project → Variables → set `HP_API_KEY` to that value → redeploy (or trust hot reload if Railway supports it for env vars).
3. Open Prompt Opinion marketplace listing → MCP integration secret → paste the same value.
4. Verify with: `curl -X POST https://health-pulse-mcp-production.up.railway.app/mcp -H "X-API-Key: <value>" -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'` — should return 200 with the 11 tools, not 401.

(On Windows, curl has SSL issues per the user's CLAUDE.md — use `node -e "fetch('https://health-pulse-mcp-production.up.railway.app/mcp', {method:'POST', headers:{'X-API-Key':'<value>','Content-Type':'application/json'}, body:JSON.stringify({jsonrpc:'2.0',id:1,method:'tools/list'})}).then(r=>r.text()).then(t=>console.log(t.slice(0,500)))"` instead.)

**Alternative (rotate-and-replace):** Generate a new strong key (`openssl rand -base64 32`), update all three locations to that value, redeploy Railway. Less risky than guessing-the-current-value.

### 1H. Risks to Mitigate (Health Pulse)

- **AI briefing took 19 s** — record click, then cut/speed up in post, OR pre-generate once before recording so cached version renders fast
- **Domo OAuth quota** — token cached 60 s; avoid >50 distinct queries in a short burst
- **Vercel cold start** — 1–3 s on first hit; pre-warm
- **MCP key drift** — see § 1G; resolve before Prompt Opinion video

---

 

## 3. Security Posture (both repos)

### 3A. Health Pulse — VERDICT: GO for public exposure (already public)

| Check                                    | Result                                     |
| ---------------------------------------- | ------------------------------------------ |
| `.env*` in `.gitignore`                  | YES + `*.pem`/`*.key` added today          |
| `.env*` ever committed                   | NO — only `.env.example` (empty values)    |
| Hardcoded `sk-…`, `AKIA…`, `ghp_…`, JWTs | NONE                                       |
| PII / customer data                      | NONE — synthetic Synthea + public CMS only |
| Live MCP unauthenticated                 | Returns 401 (auth gate active)             |
| Tracked files scanned                    | 130 — clean                                |

### 

##

---

## 5. User Action Items (Claude can't do these)

| #   | Action                                                                               | Project      | Priority                        | Est. Time |
| --- | ------------------------------------------------------------------------------------ | ------------ | ------------------------------- | --------- |
| 1   | Verify `HP_API_KEY` parity across local `.env` ↔ Railway ↔ Prompt Opinion (see § 1G) | health-pulse | HIGH (blocks marketplace video) | 10 min    |
| 2   | Record demo video (script: `assets/VIDEO-SCRIPT.md`)                                 | health-pulse | HIGH (May 11 deadline)          | 1–2 hr    |
|     |                                                                                      |              |                                 |           |
|     |                                                                                      |              |                                 |           |
| 5   | Generate logos via image model (prompts in §§ 1B + 2B)                               | both         | MED                             | 30 min    |
| 6   | Generate architecture diagrams via image model (prompts in §§ 1B + 2B)               | both         | MED                             | 30 min    |
| 7   | Generate NotebookLM Audio/Video Overviews (scripts in §§ 1C + 2C)                    | both         | MED                             | 15 min    |
| 8   | Submit on Devpost (Agents Assemble)                                                  | health-pulse | HIGH (May 11)                   | 30 min    |
|     |                                                                                      |              |                                 |           |

---

## Appendix A — Key file paths

### Health Pulse

- `health-pulse/SUBMISSION.md` — root submission packet
- `health-pulse/assets/SUBMISSION.md` — Devpost narrative
- `health-pulse/assets/VIDEO-SCRIPT.md` — dashboard recording script (132 lines)
- `health-pulse/assets/PROMPT-OPINION-DEMO-GUIDE.md` — marketplace recording (160+ lines)
- `health-pulse/assets/architecture.md` — architecture overview
- `health-pulse/docs/devpost-submission.md` — full Devpost form draft
- `health-pulse/scripts/liveness.sh` — pre-record sanity check
- `health-pulse/web/src/app/api/chat/route.ts:174-330` — chat handler
- `health-pulse/web/src/lib/data/domo-client.ts:5-51` — Domo OAuth + query
- `health-pulse/Dockerfile:9-13` — FHIR bundle copy for Railway
- `health-pulse/mcp-server/src/healthpulse_mcp/fhir_client.py:21-22` — FHIR data dir env
- `health-pulse/mcp-server/.env` — local source-of-truth for `HP_API_KEY`

### 

---

## Appendix B — Live verification commands (re-run before recording)

### Health Pulse liveness

```bash
cd C:/Users/Steve.Harlow/CascadeProjects/health-pulse && bash scripts/liveness.sh
```

### 


