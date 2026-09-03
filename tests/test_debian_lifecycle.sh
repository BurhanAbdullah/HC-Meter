#!/usr/bin/env bash
set -euo pipefail

DEB="${1:?usage: test_debian_lifecycle.sh PACKAGE.deb}"
[[ -f "$DEB" ]]
command -v dpkg >/dev/null
command -v dpkg-deb >/dev/null
command -v systemctl >/dev/null
command -v curl >/dev/null

version="$(dpkg-deb -f "$DEB" Version)"
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]

cleanup() {
  dpkg --purge syswatch >/dev/null 2>&1 || true
  systemctl daemon-reload >/dev/null 2>&1 || true
  rm -rf "${tmp:-}"
}
trap cleanup EXIT

# The release runner is disposable. Exercise the real maintainer scripts and
# systemd boundary rather than only inspecting package metadata.
dpkg -i "$DEB"
systemctl is-enabled syswatch.service
systemctl is-active syswatch.service
id syswatch

test "$(stat -c '%U:%G:%a' /var/lib/syswatch)" = 'syswatch:syswatch:750'
test "$(stat -c '%U:%G' /opt/syswatch)" = 'root:root'

grep -q '^User=syswatch$' /etc/systemd/system/syswatch.service
grep -q '^Group=syswatch$' /etc/systemd/system/syswatch.service
grep -q '^NoNewPrivileges=true$' /etc/systemd/system/syswatch.service
grep -q '^CapabilityBoundingSet=$' /etc/systemd/system/syswatch.service
grep -q '^AmbientCapabilities=$' /etc/systemd/system/syswatch.service
grep -q '^Environment=SYSWATCH_STATE_DIR=/var/lib/syswatch$' /etc/systemd/system/syswatch.service

for _ in {1..20}; do
  if curl -fsS --max-time 1 http://127.0.0.1:8080/api/health >/tmp/syswatch-health.json 2>/dev/null; then
    break
  fi
  sleep 1
done
curl -fsS --max-time 2 http://127.0.0.1:8080/api/health >/tmp/syswatch-health.json
grep -q '"' /tmp/syswatch-health.json

# Exercise an upgrade with a strictly greater version while retaining the
# installed state directory. Only the Debian control version is changed.
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
curl -fsS --max-time 2 http://127.0.0.1:8080/api/health >/tmp/syswatch-health-upgrade.json

dpkg --purge syswatch
! getent passwd syswatch >/dev/null
! getent group syswatch >/dev/null
! test -e /etc/systemd/system/syswatch.service
! test -e /usr/local/bin/syswatch
! test -e /usr/local/bin/syswatch-signal
! test -e /var/lib/syswatch

trap - EXIT
rm -rf "$tmp"
echo 'Debian install/upgrade/purge lifecycle checks passed.'
