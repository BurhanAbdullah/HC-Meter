#!/usr/bin/env bash
set -euo pipefail

DEB="${1:?usage: test_debian_lifecycle.sh PACKAGE.deb}"
[[ -f "$DEB" ]]
for command in dpkg dpkg-deb systemctl curl python3 id stat getent journalctl; do command -v "$command" >/dev/null; done

version="$(dpkg-deb -f "$DEB" Version)"
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]

tmp=""
cleanup() {
  dpkg --purge syswatch >/dev/null 2>&1 || true
  systemctl daemon-reload >/dev/null 2>&1 || true
  rm -rf "$tmp"
}
trap cleanup EXIT

assert_equal() {
  local expected="$1" actual="$2" label="$3"
  if [[ "$actual" != "$expected" ]]; then
    printf 'lifecycle assertion failed: %s\nexpected: %s\nactual:   %s\n' "$label" "$expected" "$actual" >&2
    return 1
  fi
}

health_payload_is_valid() {
  local output="$1"
  python3 - "$output" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        payload = json.load(handle)
except (OSError, json.JSONDecodeError, UnicodeDecodeError):
    raise SystemExit(1)

expected = {"ok": True, "service": "syswatch", "agent": "online"}
raise SystemExit(0 if payload == expected else 1)
PY
}

wait_for_health() {
  local output="$1"
  local attempts="${2:-30}"
  local timeout="${3:-1}"
  local ready=0
  for _ in $(seq 1 "$attempts"); do
    if curl -fsS --max-time "$timeout" http://127.0.0.1:8080/api/health >"$output" 2>/dev/null \
      && health_payload_is_valid "$output"; then
      ready=1
      break
    fi
    sleep 1
  done
  if (( ready != 1 )); then
    printf 'SYSWATCH health contract did not become ready after %s attempts.\n' "$attempts" >&2
    if [[ -s "$output" ]]; then
      printf 'Last health payload: ' >&2
      cat "$output" >&2 || true
      printf '\n' >&2
    fi
    systemctl status syswatch.service --no-pager >&2 || true
    journalctl -u syswatch.service -n 80 --no-pager >&2 || true
    return 1
  fi
}

dpkg -i "$DEB"
systemctl is-enabled syswatch.service
systemctl is-active syswatch.service
id syswatch

state_meta="$(stat -c '%U:%G:%a' /var/lib/syswatch)"
opt_meta="$(stat -c '%U:%G' /opt/syswatch)"
assert_equal 'syswatch:syswatch:750' "$state_meta" '/var/lib/syswatch ownership/mode'
assert_equal 'root:root' "$opt_meta" '/opt/syswatch ownership'
grep -q '^User=syswatch$' /etc/systemd/system/syswatch.service
grep -q '^Group=syswatch$' /etc/systemd/system/syswatch.service
grep -q '^NoNewPrivileges=true$' /etc/systemd/system/syswatch.service
grep -q '^CapabilityBoundingSet=$' /etc/systemd/system/syswatch.service
grep -q '^AmbientCapabilities=$' /etc/systemd/system/syswatch.service
grep -q '^ProtectSystem=strict$' /etc/systemd/system/syswatch.service
grep -q '^StateDirectoryMode=0750$' /etc/systemd/system/syswatch.service

wait_for_health /tmp/syswatch-health.json

tmp="$(mktemp -d)"
mkdir -p "$tmp/root/DEBIAN"
dpkg-deb --extract "$DEB" "$tmp/root"
dpkg-deb --control "$DEB" "$tmp/root/DEBIAN"
awk -v v="${version}.1" '!/^Version: /{print} /^Version: /{print "Version: " v}' "$tmp/root/DEBIAN/control" >"$tmp/control.new"
mv "$tmp/control.new" "$tmp/root/DEBIAN/control"
chmod 0755 "$tmp/root/DEBIAN/postinst" "$tmp/root/DEBIAN/postrm"
dpkg-deb --build "$tmp/root" "$tmp/upgrade.deb" >/dev/null
dpkg -i "$tmp/upgrade.deb"
systemctl is-active syswatch.service
wait_for_health /tmp/syswatch-health-upgrade.json 30 2

dpkg --purge syswatch
! getent passwd syswatch >/dev/null
! getent group syswatch >/dev/null
! test -e /etc/systemd/system/syswatch.service
! test -e /usr/local/bin/syswatch
! test -e /usr/local/bin/syswatch-signal
! test -e /var/lib/syswatch

trap - EXIT
cleanup
echo 'Debian install/upgrade/purge lifecycle checks passed with exact health contract.'
