#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
GOOD="$TMP/good"
BAD="$TMP/bad"

host_cleanup() {
  set +e
  sudo systemctl disable --now syswatch.service >/dev/null 2>&1 || true
  sudo rm -f /etc/systemd/system/syswatch.service /usr/local/bin/syswatch /usr/local/bin/syswatch-signal
  sudo rm -rf /opt/syswatch /var/lib/syswatch
  if getent passwd syswatch >/dev/null; then sudo userdel syswatch >/dev/null 2>&1 || true; fi
  if getent group syswatch >/dev/null; then sudo groupdel syswatch >/dev/null 2>&1 || true; fi
  sudo systemctl daemon-reload >/dev/null 2>&1 || true
  set -e
}

cleanup() {
  set +e
  host_cleanup
  rm -rf "$TMP"
}
trap cleanup EXIT

assert_absent() {
  local path="$1"
  if [[ -e "$path" ]]; then
    echo "unexpected installer residue: $path" >&2
    return 1
  fi
}

# Every CI job gets an isolated runner, but start from a deliberately known
# state so this test cannot accidentally pass because of pre-existing files.
host_cleanup

# Build local repositories so the lifecycle test never depends on an external
# network clone after checkout.
git clone -q "$ROOT" "$GOOD"
git clone -q "$ROOT" "$BAD"
git -C "$BAD" config user.name "SYSWATCH CI"
git -C "$BAD" config user.email "ci@example.invalid"
python3 - "$BAD/syswatch/api/server.py" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "return self.send_json({'ok': True, 'service': 'syswatch', 'agent': 'online'})"
new = "return self.send_json({'ok': False, 'service': 'syswatch', 'agent': 'degraded'}, 503)"
if old not in text:
    raise SystemExit("health endpoint fixture not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY
git -C "$BAD" add syswatch/api/server.py
git -C "$BAD" commit -q -m "test fixture: unhealthy service"

# 1. Failed first install must return the runner to the exact no-install state.
if sudo env SYSWATCH_REPO="$BAD" SYSWATCH_REF=main bash "$ROOT/install.sh"; then
  echo "unhealthy first install unexpectedly succeeded" >&2
  exit 1
fi
assert_absent /opt/syswatch
assert_absent /var/lib/syswatch
assert_absent /etc/systemd/system/syswatch.service
assert_absent /usr/local/bin/syswatch
assert_absent /usr/local/bin/syswatch-signal
! getent passwd syswatch >/dev/null
! getent group syswatch >/dev/null

# 2. Establish a known-good installation and persistent state.
sudo env SYSWATCH_REPO="$GOOD" SYSWATCH_REF=main bash "$ROOT/install.sh"
sudo systemctl is-enabled syswatch.service >/dev/null
sudo systemctl is-active syswatch.service >/dev/null
python3 - <<'PY'
import json
import urllib.request
with urllib.request.urlopen("http://127.0.0.1:8080/api/health", timeout=2) as response:
    payload = json.load(response)
assert response.status == 200
assert payload == {"ok": True, "service": "syswatch", "agent": "online"}
PY

good_commit="$(git -C /opt/syswatch rev-parse HEAD)"
printf 'preserve-me\n' | sudo tee /var/lib/syswatch/rollback-marker >/dev/null
sudo chown syswatch:syswatch /var/lib/syswatch/rollback-marker
cp /etc/systemd/system/syswatch.service "$TMP/service.before"
cp /usr/local/bin/syswatch "$TMP/bin.before"
cp /usr/local/bin/syswatch-signal "$TMP/signal.before"

# 3. A failed upgrade must restore code, state, wrappers, unit and runtime state.
if sudo env SYSWATCH_REPO="$BAD" SYSWATCH_REF=main bash "$ROOT/install.sh"; then
  echo "unhealthy upgrade unexpectedly succeeded" >&2
  exit 1
fi

sudo systemctl is-enabled syswatch.service >/dev/null
sudo systemctl is-active syswatch.service >/dev/null
[[ "$(git -C /opt/syswatch rev-parse HEAD)" == "$good_commit" ]]
[[ "$(cat /var/lib/syswatch/rollback-marker)" == "preserve-me" ]]
cmp -s "$TMP/service.before" /etc/systemd/system/syswatch.service
cmp -s "$TMP/bin.before" /usr/local/bin/syswatch
cmp -s "$TMP/signal.before" /usr/local/bin/syswatch-signal
python3 - <<'PY'
import json
import urllib.request
with urllib.request.urlopen("http://127.0.0.1:8080/api/health", timeout=2) as response:
    payload = json.load(response)
assert response.status == 200
assert payload == {"ok": True, "service": "syswatch", "agent": "online"}
PY

echo "Standalone installer first-install and failed-upgrade rollback checks passed."
