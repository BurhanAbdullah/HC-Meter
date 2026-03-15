#!/usr/bin/env bash

echo
echo "════ SYSTEM HEALTH ════"

cpu=$(top -bn1 | awk '/Cpu/ {print int($2+$4)}')
mem=$(free | awk '/Mem/ {printf("%.0f"), $3/$2*100}')

echo "CPU Usage: $cpu%"
echo "Memory Usage: $mem%"

if [ "$cpu" -gt 80 ]; then
echo "⚠ High CPU detected"
add_score 10
fi

if [ "$mem" -gt 80 ]; then
echo "⚠ High memory usage"
add_score 10
fi
