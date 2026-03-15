# HealthPulse AI

Healthcare performance intelligence MCP server + dashboard for the Agents Assemble hackathon.

## Architecture
- `mcp-server/` — Python MCP server with 11 tools (primary deliverable)
- `scripts/` — Data pipeline (CMS → Domo) + Synthea generator
- `web/` — Next.js dashboard with 7 pages, chat, AI briefing, PDF export
- `data/raw/` — Downloaded CMS CSVs (gitignored)
- `data/reference/` — Census FIPS crosswalk (committed)
- `data/synthea/` — 100 synthetic FHIR patients (committed)

## Commands
- MCP server: `cd mcp-server && pip install -e ".[dev]" && python -m healthpulse_mcp.server`
- Tests (MCP): `cd mcp-server && pytest` (243 tests)
- Data load: `cd scripts && python load_cms_data.py`
- Dashboard: `cd web && npm install && npm run dev`
- Tests (web): `cd web && npm test` (63 tests)

## MCP Tools (11)
quality_monitor, care_gap_finder, equity_detector, facility_benchmark,
executive_briefing, state_ranking, cross_cutting_analysis,
patient_risk_profile, patient_cohort_analysis, patient_experience, cost_efficiency

## Key Constraints
- Domo SQL: `FROM table` (literal), use `<>` not `!=`, no JOINs/subqueries
- SHARP headers: X-FHIR-Server-URL, X-Patient-ID, X-FHIR-Access-Token
- No PHI — CMS data is de-identified aggregate, Synthea is synthetic
- MCP server must NOT call Claude — returns structured data for platform LLM
- Docker: pip install puts code in site-packages, use HP_SYNTHEA_DATA_DIR env var for FHIR data path
- Vercel env vars: use `printf` not `echo` when piping to `vercel env add` (avoids trailing \n)

## Deployments
- Railway MCP: https://health-pulse-mcp-production.up.railway.app/mcp
- Vercel Dashboard: https://web-umber-alpha-41.vercel.app
- GitHub: https://github.com/sgharlow/health-pulse
