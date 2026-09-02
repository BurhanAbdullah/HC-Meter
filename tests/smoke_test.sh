#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${SYSWATCH_TEST_PORT:-18080}"
python3 -m py_compile "$ROOT/syswatch/api/server.py"
SYSWATCH_PORT="$PORT" python3 "$ROOT/syswatch/api/server.py" >/tmp/syswatch-test.log 2>&1 &
PID=$!
trap 'kill "$PID" 2>/dev/null || true' EXIT
for i in {1..20}; do curl -fsS "http://127.0.0.1:$PORT/api/health" >/dev/null && break; sleep .2; done
curl -fsS "http://127.0.0.1:$PORT/api/metrics" | grep -q '"cpu"'
curl -fsS "http://127.0.0.1:$PORT/" | grep -q 'SYSWATCH PRO'
echo "SYSWATCH smoke test passed"
