#!/usr/bin/env bash

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

while true
do
clear

echo "╔══════════════════════════════════════════════╗"
echo "║                SYSWATCH LIVE                 ║"
echo "║          Real-Time Security Monitor          ║"
echo "╚══════════════════════════════════════════════╝"
echo

# CPU
cpu=$(top -bn1 | grep "Cpu(s)" | awk '{print int($2)}')
echo "CPU Usage: $cpu%"

# Memory
mem=$(free | awk '/Mem:/ {printf("%d"), $3/$2*100}')
echo "Memory Usage: $mem%"

# Disk
disk=$(df / | awk 'NR==2 {print $5}')
echo "Disk Usage: $disk"

echo
echo "Open Ports:"
ss -tuln | awk 'NR>1 {print $5}' | cut -d: -f2 | sort -n | uniq

echo
echo "Top Processes:"
ps -eo pid,comm,%cpu --sort=-%cpu | head -n 6

echo
echo "Threat Indicators:"
grep -E "nc -l|bash -i|curl http|wget http" -r "$HOME" 2>/dev/null | head -n 3

echo
echo "Press CTRL+C to exit"

sleep 3
done
