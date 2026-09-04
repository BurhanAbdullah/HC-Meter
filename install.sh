#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="syswatch"
PREFIX="/opt/syswatch"
STATE_DIR="/var/lib/syswatch"
SERVICE_USER="syswatch"
SERVICE_GROUP="syswatch"
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
command -v useradd >/dev/null || { echo "useradd is required"; exit 1; }
command -v groupadd >/dev/null || { echo "groupadd is required"; exit 1; }
command -v getent >/dev/null || { echo "getent is required"; exit 1; }

# Ref names are accepted for convenience, but shell metacharacters and
# ambiguous revisions are rejected before any host mutation occurs.
git check-ref-format --allow-onelevel "$REF" >/dev/null 2>&1 || {
  echo "Invalid SYSWATCH_REF: $REF" >&2
  exit 1
}

TMP="$(mktemp -d)"
BACKUP=""
STATE_BACKUP=""
SWAPPED=0
CREATED_GROUP=0
CREATED_USER=0
STATE_CREATED=0
trap 'rm -rf "$TMP"' EXIT

rollback() {
  set +e
  systemctl disable --now "$APP_NAME.service" >/dev/null 2>&1 || true
  rm -rf "$PREFIX"
  if [[ -n "$BACKUP" && -d "$BACKUP" ]]; then
    mv "$BACKUP" "$PREFIX"
  fi

  # Restore the state boundary exactly as it existed before installation.
  rm -rf "$STATE_DIR"
  if [[ -n "$STATE_BACKUP" && -d "$STATE_BACKUP" ]]; then
    mv "$STATE_BACKUP" "$STATE_DIR"
  fi

  systemctl daemon-reload >/dev/null 2>&1 || true
  if [[ -d "$PREFIX" ]]; then
    systemctl enable --now "$APP_NAME.service" >/dev/null 2>&1 || true
  fi

  if [[ "$STATE_CREATED" -eq 1 && ! -d "$STATE_DIR" ]]; then
    true
  fi
  if [[ "$CREATED_USER" -eq 1 ]] && getent passwd "$SERVICE_USER" >/dev/null; then
    userdel "$SERVICE_USER" >/dev/null 2>&1 || true
  fi
  if [[ "$CREATED_GROUP" -eq 1 ]] && getent group "$SERVICE_GROUP" >/dev/null; then
    groupdel "$SERVICE_GROUP" >/dev/null 2>&1 || true
  fi
}

on_error() {
  local rc=$?
  if [[ "$SWAPPED" -eq 1 || "$CREATED_USER" -eq 1 || "$CREATED_GROUP" -eq 1 || "$STATE_CREATED" -eq 1 ]]; then
    echo "SYSWATCH installation failed; restoring the previous installation." >&2
    rollback
  fi
  exit "$rc"
}
trap on_error ERR

# The daemon never needs a login shell or administrative identity.
if ! getent group "$SERVICE_GROUP" >/dev/null; then
  groupadd --system "$SERVICE_GROUP"
  CREATED_GROUP=1
fi
if ! getent passwd "$SERVICE_USER" >/dev/null; then
  useradd --system --gid "$SERVICE_GROUP" --home-dir "$STATE_DIR" --no-create-home --shell /usr/sbin/nologin "$SERVICE_USER"
  CREATED_USER=1
fi
if [[ ! -d "$STATE_DIR" ]]; then
  install -d -m 0750 -o "$SERVICE_USER" -g "$SERVICE_GROUP" "$STATE_DIR"
  STATE_CREATED=1
fi

# Snapshot the persistent state before any migration or service change.
if [[ -d "$STATE_DIR" ]]; then
  STATE_BACKUP="$TMP/state-backup"
  cp -a "$STATE_DIR" "$STATE_BACKUP"
fi

CLONE="$TMP/syswatch"
git clone --depth 1 --branch "$REF" "$REPO" "$CLONE" >/dev/null 2>&1
git -C "$CLONE" rev-parse --verify HEAD >/dev/null

# Stage the complete version before touching the active installation.
STAGED="$TMP/installed"
mkdir -p "$STAGED"
cp -a "$CLONE/." "$STAGED/"

# Preserve the legacy in-tree runtime on first upgrade into the dedicated
# service state directory. Existing protected state is never regenerated here.
if [[ -d "$PREFIX/runtime" ]]; then
  cp -a "$PREFIX/runtime/." "$STATE_DIR/"
  chown -R "$SERVICE_USER:$SERVICE_GROUP" "$STATE_DIR"
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
export SYSWATCH_STATE_DIR="${SYSWATCH_STATE_DIR:-/var/lib/syswatch}"
exec /opt/syswatch/syswatch/agents/feed_signal.sh "$@"
EOF
chmod 0755 "$SIGNAL_BIN"

cat > "$SERVICE" <<EOF
[Unit]
Description=SYSWATCH Pro Host Security Monitor
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$PREFIX
Environment=SYSWATCH_STATE_DIR=$STATE_DIR
ExecStart=/usr/bin/python3 $PREFIX/syswatch/api/server.py
Restart=on-failure
RestartSec=3
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=read-only
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true
RestrictRealtime=true
CapabilityBoundingSet=
AmbientCapabilities=
ReadWritePaths=$STATE_DIR
StateDirectory=syswatch
StateDirectoryMode=0750

[Install]
WantedBy=multi-user.target
EOF
chmod 0644 "$SERVICE"
chown -R root:root "$PREFIX"

cat > "$PREFIX/uninstall.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "$(id -u)" -ne 0 ]]; then echo "Run with sudo"; exit 1; fi
systemctl disable --now syswatch.service 2>/dev/null || true
rm -f /etc/systemd/system/syswatch.service /usr/local/bin/syswatch /usr/local/bin/syswatch-signal
rm -rf /opt/syswatch /var/lib/syswatch
if getent passwd syswatch >/dev/null; then userdel syswatch 2>/dev/null || true; fi
if getent group syswatch >/dev/null; then groupdel syswatch 2>/dev/null || true; fi
systemctl daemon-reload
echo "SYSWATCH removed."
EOF
chmod 0755 "$PREFIX/uninstall.sh"

systemctl daemon-reload
systemctl enable --now "$APP_NAME.service"

# Local health verification is release-blocking. The API is intentionally
# bound to loopback, so this does not expose a remote validation path. Require
# the application health contract itself, not merely an HTTP response.
python3 - <<'PY'
import json
import time
import urllib.error
import urllib.request

url = "http://127.0.0.1:8080/api/health"
last = None
for _ in range(30):
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            if response.status != 200:
                raise RuntimeError(f"unexpected HTTP status {response.status}")
            payload = json.load(response)
            if (
                payload.get("ok") is True
                and payload.get("service") == "syswatch"
                and payload.get("agent") == "online"
            ):
                raise SystemExit(0)
            raise RuntimeError(f"unexpected health payload: {payload!r}")
    except (OSError, urllib.error.URLError, json.JSONDecodeError, UnicodeDecodeError, RuntimeError) as exc:
        last = exc
        time.sleep(1)
raise SystemExit(f"SYSWATCH health check failed: {last}")
PY

# The new installation is healthy; discard rollback snapshots only now.
if [[ -n "$BACKUP" && -d "$BACKUP" ]]; then
  rm -rf "$BACKUP"
fi
if [[ -n "$STATE_BACKUP" && -d "$STATE_BACKUP" ]]; then
  rm -rf "$STATE_BACKUP"
fi
SWAPPED=0
CREATED_USER=0
CREATED_GROUP=0
STATE_CREATED=0

printf '\nSYSWATCH PRO installed successfully.\n'
printf 'Version/ref: %s\n' "$REF"
printf 'Dashboard: http://127.0.0.1:8080\n'
printf 'Commands: syswatch {start|stop|restart|status|logs|open|uninstall}\n'
printf 'Signal bridge: syswatch-signal SIGNAL "details"\n'
