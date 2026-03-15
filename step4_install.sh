#!/usr/bin/env bash
# ── STEP 4: SYSWATCH TOOL INSTALLER ─────────────────────

set -e

TARGET_DIR="$HOME/.local/bin"
TARGET="$TARGET_DIR/syswatch"

echo "╔══════════════════════════════════════════════════════╗"
echo "║  SYSWATCH — TOOL INSTALLER                           ║"
echo "╚══════════════════════════════════════════════════════╝"
echo

mkdir -p "$TARGET_DIR"

echo "Installing syswatch to $TARGET"

cat <<'EOF' > "$TARGET"
#!/usr/bin/env bash

case "$1" in
    once)
        ./step3_vulnscore.sh
        ;;
    vitals)
        ./step1_vitals.sh
        ;;
    security)
        ./step2_security.sh
        ;;
    score)
        ./step3_vulnscore.sh
        ;;
    help)
        echo "SYSWATCH COMMANDS"
        echo
        echo "syswatch           Full monitor"
        echo "syswatch once      Single run"
        echo "syswatch vitals    Hardware stats"
        echo "syswatch security  Security checks"
        echo "syswatch score     Vulnerability score"
        ;;
    uninstall)
        rm -f "$HOME/.local/bin/syswatch"
        echo "Syswatch removed"
        ;;
    *)
        ./step3_vulnscore.sh
        ;;
esac
EOF

chmod +x "$TARGET"

echo
echo "✔ syswatch installed."

echo
echo "Add this to your ~/.zshrc if needed:"
echo 'export PATH="$HOME/.local/bin:$PATH"'

echo
echo "Run:"
echo "syswatch help"

