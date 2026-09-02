#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY="$ROOT/syswatch/agent/causal_engine.py"
usage(){ echo 'Usage: feed_signal.sh SIGNAL [DETAIL]'; echo 'Example: feed_signal.sh NEW-PORT "Port 2222 opened"'; }
[[ $# -ge 1 ]] || { usage; exit 2; }
case "$1" in --demo)
 python3 - "$PY" <<'PY'
import sys,time
sys.path.insert(0,__import__('os').path.dirname(sys.argv[1])); from causal_engine import engine
for s,d in [('new_port','Port 2222 opened'),('reverse_shell','bash spawned'),('file_write_tmp','/tmp/.implant written'),('cron_change','scheduled task changed'),('outbound_c2','external connection')]: engine.ingest(s,d); time.sleep(.05)
import json; print(json.dumps(engine.summary(),indent=2))
PY
;;
*)
 SIG="$(printf '%s' "$1" | tr '[:upper:]-' '[:lower:]_')"; DETAIL="${2:-}"
 python3 - "$PY" "$SIG" "$DETAIL" <<'PY'
import sys,os,json
sys.path.insert(0,os.path.dirname(sys.argv[1])); from causal_engine import engine
print(json.dumps(engine.ingest(sys.argv[2],sys.argv[3]),indent=2)); print(json.dumps(engine.summary(),indent=2))
PY
;; esac