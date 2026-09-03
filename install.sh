#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="syswatch"
PREFIX="/opt/syswatch"
BIN="/usr/local/bin/syswatch"
SIGNAL_BIN="/usr/local/bin/syswatch-signal"
SERVICE="/etc/systemd/system/syswatch.service"
REPO="${SYSWATCH_REPO:-https://github.com/BurhanAbdullah/Syswatch.git}"
REF="${SYSWATCH_REF:-main}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Please run: sudo SYSWATCH_REF=<tag-or-branch> ./install.sh"
  exit 1
fi

command -v git >/dev/null || { echo "git is required"; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }
command -v systemctl >/dev/null || { echo "systemd/systemctl is required"; exit 1; }

git check-ref-format --allow-onelevel "$REF" >/dev/null 2>&1 || {
  echo "Invalid SYSWATCH_REF: $REF" >&2
  exit 1
}

TMP="$(mktemp -d)"
BACKUP=""
SWAPPED=0
trap 'rm -rf "$TMP"' EXIT

rollback() {
  set +e
  systemctl disable --now "$APP_NAME.service" >/dev/null 2>&1 || true
  rm -rf "$PREFIX"
  if [[ -n "$BACKUP" && -d "$BACKUP" ]]; then
    mv "$BACKUP" "$PREFIX"
  fi
  systemctl daemon-reload >/dev/null 2>&1 || true
  if [[ -d "$PREFIX" ]]; then
    systemctl enable --now "$APP_NAME.service" >/dev/null 2>&1 || true
  fi
}

on_error() {
  local rc=$?
  if [[ "$SWAPPED" -eq 1 ]]; then
    echo "SYSWATCH installation failed; restoring the previous installation." >&2
    rollback
  fi
  exit "$rc"
}
trap on_error ERR

CLONE="$TMP/syswatch"
git clone --depth 1 --branch "$REF" "$REPO" "$CLONE" >/dev/null 2>&1
git -C "$CLONE" rev-parse --verify HEAD >/dev/null

# Stage the complete version before touching the active installation.
STAGED="$TMP/installed"
mkdir -p "$STAGED"
cp -a "$CLONE/." "$STAGED/"

# Preserve existing runtime state during an upgrade. The application itself
# remains responsible for validating security-sensitive state before use.
if [[ -d "$PREFIX/runtime" ]]; then
  mkdir -p "$STAGED/runtime"
  cp -a "$PREFIX/runtime/." "$STAGED/runtime/"
fi

# Stop the active service only after a complete staged tree exists.
systemctl disable --now "$APP_NAME.service" >/dev/null 2>&1 || true

if [[ -e "$PREFIX" ]]; then
  BACKUP="${PREFIX}.rollback.$$"
  mv "$PREFIX" "$BACKUP"
fi
mv "$STAGED" "$PREFIX"
SWAPPED=1

cat > "$BIN" <<'EOF'
#!/usr/bin/env bash
set -e
case "${1:-start}" in
  start) systemctl start syswatch.service; echo "SYSWATCH is running at http://127.0.0.1:8080" ;;
  stop) systemctl stop syswatch.service ;;
  restart) systemctl restart syswatch.service ;;
  status) systemctl --no-pager status syswatch.service ;;
  logs) journalctl -u syswatch.service -n 100 --no-pager ;;
  open) xdg-open http://127.0.0.1:8080 2>/dev/null || true ;;
  uninstall) /opt/syswatch/uninstall.sh ;;
  *) echo "Usage: syswatch {start|stop|restart|status|logs|open|uninstall}"; exit 2 ;;
esac
EOF
chmod 0755 "$BIN"

cat > "$SIGNAL_BIN" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec /opt/syswatch/syswatch/agents/feed_signal.sh "$@"
EOF
chmod 0755 "$SIGNAL_BIN"

cat > "$SERVICE" <<EOF
[Unit]
Description=SYSWATCH Pro Host Security Monitor
After=network.target

[Service]
Type=simple
WorkingDirectory=$PREFIX
ExecStart=/usr/bin/python3 $PREFIX/syswatch/api/server.py
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
ProtectHome=read-only

[Install]
WantedBy=multi-user.target
EOF
chmod 0644 "$SERVICE"

cat > "$PREFIX/uninstall.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "$(id -u)" -ne 0 ]]; then echo "Run with sudo"; exit 1; fi
systemctl disable --now syswatch.service 2>/dev/null || true
rm -f /etc/systemd/system/syswatch.service /usr/local/bin/syswatch /usr/local/bin/syswatch-signal
rm -rf /opt/syswatch
systemctl daemon-reload
echo "SYSWATCH removed."
EOF
chmod 0755 "$PREFIX/uninstall.sh"

systemctl daemon-reload
systemctl enable --now "$APP_NAME.service"

# Local health verification is release-blocking. The API is intentionally
# bound to loopback, so this does not expose a remote validation path.
python3 - <<'PY'
import time
import urllib.error
import urllib.request

url = "http://127.0.0.1:8080/"
last = None
for _ in range(20):
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            if 200 <= response.status < 500:
                raise SystemExit(0)
    except (OSError, urllib.error.URLError) as exc:
        last = exc
        time.sleep(0.5)
raise SystemExit(f"SYSWATCH health check failed: {last}")
PY

# The new installation is healthy; discard the rollback tree only now.
if [[ -n "$BACKUP" && -d "$BACKUP" ]]; then
  rm -rf "$BACKUP"
fi
SWAPPED=0

printf '\nSYSWATCH PRO installed successfully.\n'
printf 'Version/ref: %s\n' "$REF"
printf 'Dashboard: http://127.0.0.1:8080\n'
printf 'Commands: syswatch {start|stop|restart|status|logs|open|uninstall}\n'
printf 'Signal bridge: syswatch-signal SIGNAL "details"\n'
