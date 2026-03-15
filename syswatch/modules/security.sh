#!/usr/bin/env bash

# Colors
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RESET="\033[0m"

print_section() {
    echo
    echo -e "${CYAN}════════════════ $1 ════════════════${RESET}"
}

ok() {
    echo -e "${GREEN}✔ $1${RESET}"
}

warn() {
    echo -e "${YELLOW}⚠ $1${RESET}"
}

alert() {
    echo -e "${RED}✖ $1${RESET}"
}

print_section "SECURITY OVERVIEW"

# Failed logins
failed=$(grep -i "failed password" /var/log/auth.log 2>/dev/null | wc -l)

if [ "$failed" -eq 0 ]; then
    ok "No failed login attempts detected"
else
    warn "$failed failed login attempts detected"
fi

# Listening ports
print_section "OPEN NETWORK PORTS"

ss -tuln | awk 'NR>1 {print $5}' | sed 's/.*://' | sort -n | uniq | head -n 10

# Firewall
print_section "FIREWALL STATUS"

if command -v ufw >/dev/null 2>&1; then
    status=$(ufw status | head -n 1)
    echo "$status"
else
    warn "UFW firewall not installed"
fi

# SUID binaries
print_section "SUID BINARIES"

suid_count=$(find / -perm -4000 -type f 2>/dev/null | wc -l)

echo "Total SUID binaries: $suid_count"

find / -perm -4000 -type f 2>/dev/null | head -n 10

# Cron persistence
print_section "CRON JOB PERSISTENCE"

cron=$(crontab -l 2>/dev/null)

if [ -z "$cron" ]; then
    ok "No user cron jobs detected"
else
    warn "User cron jobs present:"
    echo "$cron"
fi

# System cron directories
echo
echo "System cron directories:"
ls /etc/cron* 2>/dev/null

# Startup persistence
print_section "STARTUP FILES"

for f in ~/.bashrc ~/.profile ~/.zshrc; do
    if [ -f "$f" ]; then
        echo "$f"
    fi
done

# Suspicious startup commands (ignore comments)
print_section "SUSPICIOUS STARTUP COMMANDS"

sus=$(grep -Ei "curl|wget|nc |bash -i|/dev/tcp|python -c" ~/.bashrc ~/.profile ~/.zshrc 2>/dev/null | grep -v "^#")

if [ -z "$sus" ]; then
    ok "No suspicious startup commands detected"
else
    alert "Possible persistence commands:"
    echo "$sus"
fi

print_section "THREAT INDICATORS"

miners=$(ps aux | grep -Ei "xmrig|minerd|cryptonight" | grep -v grep)

if [ -z "$miners" ]; then
    ok "No crypto miners detected"
else
    alert "Possible crypto miner running:"
    echo "$miners"
fi

shells=$(ps aux | grep -E "nc -l|bash -i|/dev/tcp" | grep -v grep)

if [ -z "$shells" ]; then
    ok "No reverse shell indicators detected"
else
    alert "Possible reverse shell activity:"
    echo "$shells"
fi
