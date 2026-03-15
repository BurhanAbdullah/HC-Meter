#!/usr/bin/env bash

RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RESET="\033[0m"

cpu=$(top -bn1 | awk '/Cpu/ {print int($2+$4)}')
mem=$(free | awk '/Mem/ {printf("%.0f"), $3/$2*100}')
disk=$(df / | awk 'NR==2 {print $5}' | tr -d '%')

bar () {
v=$1
f=$((v/5))
e=$((20-f))

printf "["
printf "%0.s█" $(seq 1 $f)
printf "%0.s░" $(seq 1 $e)
printf "] %s%%\n" "$v"
}

clear

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════╗"
echo "║                  SYSWATCH PRO                    ║"
echo "║        System Security Monitoring Console        ║"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${RESET}"

echo
echo "SYSTEM HEALTH"
echo

printf "CPU    "
bar "$cpu"

printf "MEM    "
bar "$mem"

printf "DISK   "
bar "$disk"

echo
echo "TOP CPU PROCESSES"
ps -eo pid,comm,%cpu --sort=-%cpu | head -n 6

echo
echo "NETWORK PORTS"
ss -tuln | awk 'NR>1 {print $5}' | sed 's/.*://' | sort -n | uniq

echo
echo "THREAT INDICATORS"

miner=$(ps aux | grep -Ei "xmrig|minerd|cryptominer" | grep -v grep)

if [ -z "$miner" ]; then
echo -e "${GREEN}✔ No crypto miners detected${RESET}"
else
echo -e "${RED}⚠ Possible crypto miner running${RESET}"
fi

shell=$(ps aux | grep -E "nc -l|bash -i|/dev/tcp" | grep -v grep)

if [ -z "$shell" ]; then
echo -e "${GREEN}✔ No reverse shell indicators${RESET}"
else
echo -e "${RED}⚠ Possible reverse shell detected${RESET}"
fi

risk=0

if [ "$cpu" -gt 80 ]; then
risk=$((risk+30))
fi

if [ "$mem" -gt 80 ]; then
risk=$((risk+30))
fi

if [ "$disk" -gt 80 ]; then
risk=$((risk+20))
fi

echo
echo "SYSTEM RISK SCORE"

if [ "$risk" -lt 30 ]; then
echo -e "${GREEN}LOW RISK ($risk)${RESET}"
elif [ "$risk" -lt 60 ]; then
echo -e "${YELLOW}MEDIUM RISK ($risk)${RESET}"
else
echo -e "${RED}HIGH RISK ($risk)${RESET}"
fi
