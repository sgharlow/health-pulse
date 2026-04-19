# Live MCP Demo Setup — Claude Code + HealthPulse Railway

One-pager for wiring Claude Code to the live HealthPulse MCP server so you
can record a real agent invoking the 11 tools against live CMS / CDC data.
This is Option B from the recording-readiness audit — a second authenticity
layer on top of the already-real dashboard walkthrough.

## Prerequisites

- Claude Code CLI (`claude` on PATH, `claude --version` ≥ 2.x)
- Network to `health-pulse-mcp-production.up.railway.app`
- A valid `HP_API_KEY` — see the blocker below

## Blocker: HP_API_KEY parity

Before you can connect Claude Code to the Railway MCP, all three of these
must agree:

1. **Local environment** — available to `claude mcp add` at runtime
2. **Railway project variable `HP_API_KEY`** — what the server validates
3. **Prompt Opinion marketplace listing** — if you also want to record
   the marketplace discovery story (separate recording)

On this machine today, `mcp-server/.env` has `HP_API_KEY=` empty. You have
two paths:

### Path A — read the canonical value from Railway, propagate

1. Open Railway → `health-pulse-mcp-production` → Variables
2. Copy the `HP_API_KEY` value
3. Paste into `mcp-server/.env` locally (do NOT commit — the file is
   gitignored)
4. Use that same value in step 2 below

### Path B — rotate a new canonical value

```bash
NEW_KEY=$(openssl rand -base64 32)
echo "$NEW_KEY"
# Save it somewhere safe — password manager or your .env
# Then:
#   - paste into Railway variables, redeploy (or hot-reload if supported)
#   - paste into local mcp-server/.env
#   - (optional) paste into Prompt Opinion marketplace integration secrets
```

### Verify parity before registering Claude Code

```bash
KEY="paste-the-canonical-value-here"

node -e "
fetch('https://health-pulse-mcp-production.up.railway.app/mcp', {
  method:'POST',
  headers:{'Content-Type':'application/json','X-API-Key':'$KEY'},
  body:JSON.stringify({jsonrpc:'2.0',id:1,method:'tools/list'})
}).then(r => r.json()).then(j => {
  console.log('tools:', (j.result?.tools || []).length);
})
"
# Expected: tools: 11
# If you see tools: 0 or an error object, the key is wrong.
```

## Register the MCP server with Claude Code

Once parity is verified, register via the HTTP+header transport:

```bash
claude mcp add --transport http health-pulse \
  https://health-pulse-mcp-production.up.railway.app/mcp \
  --header "X-API-Key: <paste-the-canonical-value>"
```

Verify:

```bash
claude mcp list
# Expected: health-pulse: https://...up.railway.app/mcp - ✓ Connected

claude mcp get health-pulse
# Expected: 11 tools listed
```

## Recording the live investigation

```bash
claude
# Paste the prompt from demo/live_investigation.md
```

Expect ~5–8 minutes of real tool calls against live CMS/CDC data. The
agent's specific wording will vary per run — narrate the architecture
(11 typed tools, SHARP-on-MCP headers, FHIR integration) rather than the
exact English responses.

## Integration with the dashboard recording

Option B for health-pulse is strongest as a **second segment**, not a
replacement for the dashboard take:

- **Segment 1**: `walkthrough.mp4` (already recorded) — the visual
  product story: 11 tools visible in the hub KPI strip, chat demos
  tool-routing, equity page, briefing → AI narrative.
- **Segment 2** (this): Claude Code terminal showing 11 MCP tools
  listed and invoked directly against the Railway endpoint — proves
  the tools are real and agent-discoverable, not just UI plumbing.

Record Segment 2 in a clean terminal with the chat interface open
beside it on a second monitor, so you can show the same question asked
two ways (chat UI vs Claude Code MCP) returning structurally similar
answers.

## Cleanup (after recordings are done)

```bash
claude mcp remove health-pulse
# Rotate HP_API_KEY if you exposed it in any recording
```

## Why this is genuinely real

| Claim from submission | What live recording demonstrates |
|---|---|
| 11 MCP tools | `claude mcp get health-pulse` shows them; Claude can enumerate them |
| Agent-discoverable via MCP | Claude Code's tool picker routes to them without any HealthPulse-specific integration code |
| Real CMS data | Tool outputs cite facility IDs and numbers that match `/api/*` live responses |
| Tools work in any agent | This IS a different agent (Claude Code ≠ the Vercel chat UI) and it works unchanged |
| SHARP-on-MCP FHIR headers | `patient_*` tools propagate FHIR context via headers — if you include the `X-Patient-ID` and `X-FHIR-Server-URL` headers in a second `claude mcp add` stanza, the patient tools light up |
