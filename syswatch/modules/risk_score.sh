#!/usr/bin/env bash

cpu=$(top -bn1 | awk '/Cpu/ {print int($2+$4)}')
mem=$(free | awk '/Mem/ {printf("%.0f"), $3/$2*100}')

score=0

if [ "$cpu" -gt 80 ]; then
score=$((score+30))
fi

if [ "$mem" -gt 80 ]; then
score=$((score+30))
fi

echo
echo "════════ SYSTEM RISK SCORE ════════"

if [ "$score" -lt 30 ]; then
echo "✔ LOW RISK ($score)"
elif [ "$score" -lt 60 ]; then
echo "⚠ MEDIUM RISK ($score)"
else
echo "✖ HIGH RISK ($score)"
fi
