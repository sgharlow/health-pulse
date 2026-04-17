#!/usr/bin/env bash
# HealthPulse liveness smoke test.
#
# Verifies the two production deployments are reachable and responsive.
# Exits non-zero and prints the failing endpoint if any check fails.
# Intended to be run before the demo video recording so the USER never
# points the camera at a 500.

set -u

DASHBOARD_URL="${HEALTHPULSE_DASHBOARD_URL:-https://web-umber-alpha-41.vercel.app}"
MCP_URL="${HEALTHPULSE_MCP_URL:-https://health-pulse-mcp-production.up.railway.app/mcp}"

fail=0
# Liveness = the HTTP layer responded. We don't care what status code the
# server chose — 200, 401 (auth required), 405 (wrong method) all prove
# the server is up. Only connection failures (000) and 5xx count as down.
check() {
  local name="$1"
  local url="$2"
  local actual
  actual=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "000")
  if [[ "$actual" == "000" ]] || [[ "$actual" =~ ^5 ]]; then
    printf "  FAIL %-30s %s -> %s\n" "$name" "$url" "$actual" >&2
    fail=1
  else
    printf "  OK   %-30s %s -> %s\n" "$name" "$url" "$actual"
  fi
}

echo "HealthPulse liveness check"
echo "---------------------------"
check "Vercel dashboard (/)"   "$DASHBOARD_URL/"
# GET /mcp may return 401 (if HP_API_KEY gate is on) or 405 (if not).
# Either proves the JSON-RPC server is reachable.
check "Railway MCP (GET /mcp)" "$MCP_URL"

echo "---------------------------"
if [[ $fail -ne 0 ]]; then
  echo "LIVENESS: FAIL" >&2
  exit 1
fi
echo "LIVENESS: OK"
