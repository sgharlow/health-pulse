# HealthPulse AI

Healthcare performance intelligence MCP server for the Agents Assemble hackathon.

## Architecture
- `mcp-server/` — Python MCP server (primary deliverable)
- `scripts/` — Data pipeline (CMS → Domo)
- `web/` — Next.js dashboard (supplementary)
- `data/raw/` — Downloaded CMS CSVs (gitignored)
- `data/reference/` — Census FIPS crosswalk (committed)

## Commands
- MCP server: `cd mcp-server && pip install -e . && python -m healthpulse_mcp.server`
- Tests (MCP): `cd mcp-server && pytest`
- Data load: `cd scripts && python load_cms_data.py`
- Dashboard: `cd web && npm install && npm run dev`
- Tests (web): `cd web && npm test`

## Key Constraints
- Domo SQL: `FROM table` (literal), use `<>` not `!=`, no JOINs/subqueries
- SHARP headers: X-FHIR-Server-URL, X-Patient-ID, X-FHIR-Access-Token
- No PHI — CMS data is de-identified aggregate, Synthea is synthetic
- MCP server must NOT call Claude — returns structured data for platform LLM
