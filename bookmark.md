# HealthPulse AI — Session Bookmark

> Last updated: 2026-03-15
> Resume this checklist after the demo video is recorded.

---

## Current State

Everything is built, tested, and deployed. 313 tests passing, CI green, 11 tools live on Railway, dashboard live on Vercel, Prompt Opinion marketplace published.

| Surface | URL | Status |
|---------|-----|--------|
| MCP Server | https://health-pulse-mcp-production.up.railway.app/mcp | 11 tools live |
| Dashboard | https://web-umber-alpha-41.vercel.app | 7 pages, chat, AI briefing, PDF |
| Prompt Opinion | https://app.promptopinion.ai | Published, verified |
| GitHub | https://github.com/sgharlow/health-pulse | 36 commits, CI green |
| Devpost | https://agents-assemble.devpost.com/ | Not yet submitted |

---

## Remaining Steps (all manual)

### Step 1: Upload Video to YouTube
- Title: `HealthPulse AI — Healthcare Performance Intelligence (Agents Assemble Hackathon)`
- Visibility: **Public** or **Unlisted**
- Description: see `docs/REMAINING-STEPS.md` section 4
- Copy the YouTube URL

### Step 2: Submit on Devpost
- Go to https://agents-assemble.devpost.com/
- Create new submission
- **Project Name:** HealthPulse AI
- **Tagline:** Healthcare performance intelligence across 5,400+ US hospitals — 11 MCP tools, real CMS data, synthetic FHIR patients, conversational AI
- **About:** Copy full text from `assets/SUBMISSION.md`
- **Built With:** Python, MCP, FastMCP, Domo, Starlette, Next.js, TypeScript, Tailwind CSS, Recharts, Vitest, @anthropic-ai/sdk, @react-pdf/renderer, Railway, Vercel, Synthea
- **Try It Out:** https://app.promptopinion.ai (note: select "HealthPulse AI" in Launchpad)
- **Demo Video:** https://youtu.be/40haMLuDOIk
- **Repository:** https://github.com/sgharlow/health-pulse
- **Images:** Upload screenshots from `assets/screenshots/` (10 images)

### Step 3: Address Domo Trial Expiry (CRITICAL — before April 10)

The Domo developer trial (`steve-dev-1098525`) expires ~April 13, which is 28 days before the May 11 deadline. When it expires, all 9 Domo-backed tools break.

**Options (pick one):**

1. **Create a fresh Domo developer trial around April 10** — re-run `scripts/load_cms_data.py` to load data into the new instance, update dataset IDs in Railway env vars and Vercel env vars. Takes ~1 hour.

2. **Migrate to a secondary Domo tenant** — any existing Domo workspace with working OAuth. Prefix datasets with `hp_` and re-upload. Update env vars on Railway + Vercel. Takes ~1 hour.

3. **Contact Domo support** to extend the trial. Uncertain timeline.

**After whichever option:** Verify tools work by sending a test query in Prompt Opinion.

### Step 4: Pre-Judging Verification (before May 11)

- [ ] Send a test query in Prompt Opinion — confirm tools respond with real data
- [ ] Visit the Vercel dashboard — confirm it loads data (not errors)
- [ ] Check Railway service is running (hobby plan sleeps after inactivity — send a warmup request)
- [ ] Verify YouTube video is still accessible (Public/Unlisted)
- [ ] Verify Devpost submission is complete and visible

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `assets/SUBMISSION.md` | Full submission text (paste into Devpost "About") |
| `assets/PROMPT-OPINION-DEMO-GUIDE.md` | Demo recording script with 5 queries and timing |
| `assets/VIDEO-SCRIPT.md` | NotebookLM narration script (dashboard screenshots version) |
| `assets/architecture.md` | ASCII architecture diagram |
| `assets/screenshots/*.png` | 10 screenshots for Devpost upload |
| `docs/REMAINING-STEPS.md` | Detailed pre-submission checklist |
| `CLAUDE.md` | Project commands and constraints |

## Key Numbers (for quick reference)

| Metric | Value |
|--------|-------|
| MCP Tools | 11 |
| MCP Resources | 6 |
| Domo Datasets | 7 (233K+ rows) |
| FHIR Patients | 100 (1,002 resources) |
| CMS Hospitals | 5,426 |
| Tests | 313 (250 MCP + 63 web) |
| Dashboard Pages | 7 |
| API Routes | 6 |
| Commits | 36 |
| Deadline | May 11, 2026, 11:00 PM EDT |

## Env Vars to Update if Domo Instance Changes

These must match across Railway and Vercel:

```
DOMO_CLIENT_ID
DOMO_CLIENT_SECRET
HP_FACILITIES_DATASET_ID
HP_QUALITY_DATASET_ID
HP_READMISSIONS_DATASET_ID
HP_SAFETY_DATASET_ID
HP_EXPERIENCE_DATASET_ID
HP_COST_DATASET_ID
HP_COMMUNITY_DATASET_ID
```

On Vercel, use `printf` (not `echo`) when piping to `vercel env add` to avoid trailing newlines.
