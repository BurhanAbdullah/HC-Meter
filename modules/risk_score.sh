#!/usr/bin/env bash

score=0

cpu=$(top -bn1 | awk '/Cpu/ {print int($2+$4)}')
mem=$(free | awk '/Mem/ {printf("%.0f"), $3/$2*100}')

if [ "$cpu" -gt 80 ]; then
score=$((score+20))
fi

if [ "$mem" -gt 80 ]; then
score=$((score+20))
fi

failed=$(grep -i "failed password" /var/log/auth.log 2>/dev/null | wc -l)

if [ "$failed" -gt 5 ]; then
score=$((score+30))
fi

echo
echo "════════ SYSTEM RISK SCORE ════════"
echo "Score: $score / 100"
