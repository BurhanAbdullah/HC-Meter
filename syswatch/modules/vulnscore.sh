#!/usr/bin/env bash

cpu=$(top -bn1 | grep "Cpu(s)" | awk '{print int($2+$4)}')
mem=$(free | awk '/Mem/ {printf("%.0f"), $3/$2*100}')
disk=$(df / | awk 'NR==2 {print $5}' | tr -d '%')

score=$(( (cpu + mem + disk) / 3 ))

echo
echo "SYSWATCH — VULNERABILITY SCORE"
echo
echo "CPU: $cpu%"
echo "MEM: $mem%"
echo "DISK: $disk%"
echo
echo "Risk Score: $score%"
