# HealthPulse AI — Read-Along Walkthrough Script (2:18)

Keyed to `screenshots/walkthrough.mp4` (138.7s). **334 narration words** across 10 scenes at ~140 wpm effective cadence. Dead time (58% of the recording) is used for MCP/architecture context; active screens get minimal pointer narration.

---

## Scene-by-scene read-along

### `[0:00–0:04]` Hub landing (4s, active)

**On screen:** HealthPulse AI hero, 3 cards (Visual Analytics / Ask HealthPulse AI / Prompt Opinion Marketplace), footer: 11 MCP Tools · 7 Domo Datasets · 233K+ Records · 5,426 Hospitals · 100 Synthetic Patients · SHARP/FHIR Ready.

> **HealthPulse AI — eleven MCP tools, one healthcare platform.**

---

### `[0:05–0:34]` Chat: CA query submitted, 30s thinking (DEAD TIME — product pitch)

**On screen:** Chat page. User bubble "Show me quality anomalies in California hospitals". "HealthPulse AI is thinking…" spinner for ~30s.

> First question to the agent: show me quality anomalies in California hospitals. Behind this chat, HealthPulse isn't an app — it's a Model Context Protocol server. Eleven healthcare intelligence tools that any MCP client — Claude Desktop, Prompt Opinion, the Anthropic API, a custom agent — can invoke by name. Right now Claude is calling the `quality_monitor` tool against 233,000 rows of real CMS data, computing Z-scores across all 5,426 US hospitals. No dashboards. No thresholds. Structured output a host model can reason over.

---

### `[0:35–0:64]` CA response visible → TX query → thinking (MIXED — reading + dead)

**On screen:** Chat response with Hip/Knee Readmission Crisis, Oroville Hospital, UCI Health Los Alamitos 48% higher readmissions, Kaweah Health, 21 facilities flagged. User then types "What's the equity disparity in Texas hospitals?" — 25s thinking.

> And here's the finding. UCI Health Los Alamitos — 48 percent higher hip-and-knee readmissions than expected. Oroville and Kaweah Health flagged as repeat offenders. Not threshold alerts — statistical pattern detection across an entire state, in a single tool call. Next query: what's the equity disparity in Texas? The `equity_detector` tool is now correlating every Texas hospital's star rating against the CDC Social Vulnerability Index, county by county. Same primitive, different tool.

---

### `[0:65–0:74]` TX response + Compare request (10s, active)

**On screen:** Texas equity response — VHS Harlingen 2-star, Webb County SVI 0.98, Dallas County Paradox (Parkland 2-star vs UT Southwestern 4-star). User types "Compare UCSF Medical Center and Cleveland Clinic".

> A Dallas County paradox — vulnerable communities receiving two-star care while UT Southwestern next door runs four-star. Systemic disparity, one tool call.

---

### `[0:75–0:94]` Executive Briefing page — AI narrative generating (DEAD TIME — composability story)

**On screen:** Briefing page for CA. Performance Overview: 378 facilities, 3.01/5, 21 Quality Flags, 253 Care Gaps, 30 High-Risk Counties. Then "Generating AI executive narrative…" spinner ~15-20s.

> The `executive_briefing` tool aggregates state data into a board-ready analysis. California: 378 facilities, 3.01 average stars, 253 care gaps, 30 high-risk counties. Claude is now composing the narrative — findings, anomalies, equity, recommendations — all from a single structured tool call. PDF export ships built-in. This is agent composability in action.

---

### `[0:95–1:09]` Dashboard transition → National → CA filter (15s, active)

**On screen:** Dashboard "Loading…" (~5s) → National view (5,426 facilities, 3.08 avg, 450 flags, 29,765 measures) → CA filter (378 / 3.01 / 21 / 2,287).

> Layer two: a Next.js dashboard on top of the same tools, for humans. National view — 5,426 hospitals, 3.08 average, 450 quality flags. Filter to California and the same analysis refocuses, instantly.

---

### `[1:10–1:19]` Facilities table + UCSF search (10s, active)

**On screen:** Facilities page → full list (5,426 shown) → "UCSF" typed in search → 5 UCSF facilities, Medical Center 5-star.

> Every facility is searchable. Type UCSF — five hospitals in the system, Medical Center rating a perfect five stars across CMS quality measures.

---

### `[1:20–1:29]` Compare page: empty state → results (10s, active)

**On screen:** Compare Facilities, UCSF Medical Center (CA) vs Cleveland Clinic (OH) selected → Compare clicked → Quality Measures table (death rates, ED wait times, vaccination rates).

> Compare any two facilities head-to-head. UCSF versus Cleveland Clinic — death rates, safety scores, ED wait times, all aligned in one LLM-readable view.

---

### `[1:30–1:34]` Equity Analysis (5s, active)

**On screen:** Equity page — 5,223 facilities with SVI data, 1,708 High-SVI, +0.77 Star Rating Disparity. SVI-tier chart: Low-vuln 3.53 vs High-vuln 2.75.

> The equity page visualizes the disparity the tool computes. 0.77 stars. 1,708 high-SVI facilities.

---

### `[2:15–2:18]` Return to Hub (3-4s, close)

**On screen:** Hub landing again.

> Eleven tools. Real data. Zero PHI. Built for Agents Assemble.

---

## Total word counts by scene

| Scene | Words | Seconds | wpm |
|---|---|---|---|
| Hub intro | 10 | 4 | 150 |
| CA thinking (DEAD) | 80 | 30 | 160 |
| CA response + TX query (DEAD) | 68 | 30 | 136 |
| TX response | 22 | 10 | 132 |
| Briefing generating (DEAD) | 50 | 20 | 150 |
| Dashboard + CA filter | 31 | 15 | 124 |
| Facilities + UCSF | 24 | 10 | 144 |
| Compare | 23 | 10 | 138 |
| Equity | 14 | 5 | 168 |
| Close | 12 | 4 | 180 |
| **Total** | **334** | **138** | **~145 avg** |

---

## AI audio generation (OpenAI `tts-1-hd`)

Raw narration text lives in [`narration.txt`](./narration.txt). Generator script in [`generate-narration.mjs`](./generate-narration.mjs).

### One-time: confirm your key

```bash
export OPENAI_API_KEY=sk-...
```

### Generate at default settings (`onyx` voice, speed 0.90)

```bash
cd C:/Users/sghar/CascadeProjects/health-pulse
node assets/generate-narration.mjs
```

Writes `assets/narration.mp3`. Expected cost: ~$0.06 per generation (1,900 chars × $0.030 per 1k chars on tts-1-hd).

### Measure duration and tune

```bash
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 assets/narration.mp3
```

Target: **138.7s**. If you're over/under:

| Measured duration | Action |
|---|---|
| 136–140s | Ship it |
| < 136s (too short) | `SPEED=0.87 node assets/generate-narration.mjs` |
| > 140s (too long) | `SPEED=0.93 node assets/generate-narration.mjs` |

Try a different voice if the tone is off:

```bash
VOICE=nova node assets/generate-narration.mjs    # warm female
VOICE=echo node assets/generate-narration.mjs    # warm male
VOICE=alloy node assets/generate-narration.mjs   # neutral
```

### Mux narration onto the existing video

```bash
ffmpeg -i screenshots/walkthrough.mp4 \
       -i assets/narration.mp3 \
       -c:v copy -c:a aac -b:a 192k -shortest \
       screenshots/walkthrough_narrated.mp4
```

`-c:v copy` re-uses the original video stream (no re-encode, instant). `-shortest` trims to the shorter of the two streams — if narration is a hair long, it clips the tail of the audio rather than stretching the video.

### If you have an existing audio track you want to replace

Add `-map 0:v:0 -map 1:a:0` to explicitly select video from input 0 and audio from input 1:

```bash
ffmpeg -i screenshots/walkthrough.mp4 \
       -i assets/narration.mp3 \
       -map 0:v:0 -map 1:a:0 \
       -c:v copy -c:a aac -b:a 192k -shortest \
       screenshots/walkthrough_narrated.mp4
```

---

## Voice recommendation

**`onyx`** is the default — deep, authoritative, documentary-appropriate for a healthcare-data product. **`nova`** is the strongest alternate (warm, female, Anthropic-demo-ish tone). **`alloy`** reads more neutral/technical. Avoid `fable` (British accent may feel off for a US healthcare pitch) and `shimmer` (too light for this material).

## Dead-time design rationale

The recording has ~80s of loading/spinner time (58% of runtime). Rather than silence or filler, that time carries the submission's key talking points:

- **MCP as product primitive** (0:05–0:34) — the eleven-tool story + data scale
- **Agent composability + PDF export + structured output** (0:75–0:94) — why this wins an agent hackathon
- **Architectural context** (0:35–0:64) — equity detector + CDC SVI correlation

Active screens get one short sentence each. This pattern makes the video feel dense and considered even at 2:18.
