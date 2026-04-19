#!/usr/bin/env bash
# Smoke test the HealthPulse Railway MCP HTTP transport.
# Verifies: endpoint reachable, HP_API_KEY authenticates, 11 tools advertised.
#
# Usage:
#   HP_API_KEY=<value> bash scripts/test-live-mcp.sh

set -uo pipefail

if [ -z "${HP_API_KEY:-}" ]; then
    echo "  [FAIL] HP_API_KEY not set in env - see docs/guides/live-mcp-demo-setup.md"
    exit 1
fi

echo "=== HealthPulse Railway MCP smoke test ==="
echo

python - <<'PY'
import os, sys, json, urllib.request, urllib.error, ssl

key = os.environ['HP_API_KEY']
url = 'https://health-pulse-mcp-production.up.railway.app/mcp'
payload = json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/list'}).encode()
req = urllib.request.Request(url, data=payload, method='POST',
    headers={'Content-Type':'application/json','X-API-Key':key})

try:
    with urllib.request.urlopen(req, timeout=15) as r:
        status = r.status
        body = r.read().decode()
except urllib.error.HTTPError as e:
    status = e.code
    body = e.read().decode(errors='replace')
except Exception as e:
    print(f'  [FAIL] request failed: {e}')
    sys.exit(1)

if status != 200:
    print(f'  [FAIL] endpoint returned HTTP {status}')
    print(f'         body: {body[:300]}')
    if status == 401:
        print('         (HP_API_KEY does not match what Railway expects)')
    sys.exit(1)

print(f'  [PASS] endpoint reachable ({status})')

try:
    rpc = json.loads(body)
    tools = rpc.get('result', {}).get('tools', [])
except Exception as e:
    print(f'  [FAIL] response is not JSON-RPC: {e}')
    sys.exit(1)

if len(tools) == 11:
    print(f'  [PASS] tool registry (11 tools)')
    tool_names = sorted(t.get('name', '?') for t in tools)
    print('         ' + ', '.join(tool_names))
    sys.exit(0)
else:
    print(f'  [FAIL] expected 11 tools, got {len(tools)}')
    sys.exit(1)
PY
