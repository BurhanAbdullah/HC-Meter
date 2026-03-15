#!/usr/bin/env bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cpu=$(top -bn1 | awk '/Cpu/ {print int($2+$4)}')

echo
echo "════════ ALERT ENGINE ════════"

if [ "$cpu" -gt 90 ]; then
echo -e "${RED}⚠ CRITICAL: CPU usage $cpu%${NC}"
printf '\a'
elif [ "$cpu" -gt 70 ]; then
echo -e "${YELLOW}⚠ Warning: CPU usage $cpu%${NC}"
else
echo -e "${GREEN}✔ System load normal ($cpu%)${NC}"
fi
