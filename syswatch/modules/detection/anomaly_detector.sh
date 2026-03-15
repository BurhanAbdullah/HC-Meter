#!/usr/bin/env bash

echo
echo "INTRUSION DETECTION — SYSTEM ANOMALY"

cpu=$(top -bn1 | awk '/Cpu/ {print int($2+$4)}')

if [ "$cpu" -gt 90 ]; then
echo "[CRITICAL] Abnormal CPU usage detected ($cpu%)"
else
echo "CPU behavior normal"
fi
