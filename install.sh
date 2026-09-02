#!/usr/bin/env bash
set -euo pipefail

APP_NAME="syswatch"
PREFIX="/opt/syswatch"
BIN="/usr/local/bin/syswatch"
SIGNAL_BIN="/usr/local/bin/syswatch-signal"
SERVICE="/etc/systemd/system/syswatch.service"
REPO="https://github.com/BurhanAbdullah/Syswatch.git"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Please run: sudo ./install.sh"
  exit 1
fi

command -v git >/dev/null || { echo "git is required"; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }
command -v systemctl >/dev/null || { echo "systemd/systemctl is required"; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git clone --depth 1 "$REPO" "$TMP/syswatch" >/dev/null 2>&1
rm -rf "$PREFIX"
mkdir -p "$PREFIX"
cp -a "$TMP/syswatch/." "$PREFIX/"

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
chmod +x "$BIN"

cat > "$SIGNAL_BIN" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec /opt/syswatch/syswatch/agents/feed_signal.sh "$@"
EOF
chmod +x "$SIGNAL_BIN"

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

cat > "$PREFIX/uninstall.sh" <<'EOF'
#!/usr/bin/env bash
set -e
if [[ "$(id -u)" -ne 0 ]]; then echo "Run with sudo"; exit 1; fi
systemctl disable --now syswatch.service 2>/dev/null || true
rm -f /etc/systemd/system/syswatch.service /usr/local/bin/syswatch /usr/local/bin/syswatch-signal
rm -rf /opt/syswatch
systemctl daemon-reload
echo "SYSWATCH removed."
EOF
chmod +x "$PREFIX/uninstall.sh"

systemctl daemon-reload
systemctl enable --now syswatch.service

echo
printf 'SYSWATCH PRO installed successfully.\n'
printf 'Dashboard: http://127.0.0.1:8080\n'
printf 'Commands: syswatch {start|stop|restart|status|logs|open|uninstall}\n'
printf 'Signal bridge: syswatch-signal SIGNAL "details"\n'
