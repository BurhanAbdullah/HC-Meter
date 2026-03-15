#!/usr/bin/env bash

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVENT_LOG="$BASE_DIR/logs/events.log"

echo
echo "════ ANOMALY DETECTION ENGINE ════"

cpu=$(top -bn1 | grep "Cpu(s)" | awk '{print int($2)}')
mem=$(free | awk '/Mem:/ {printf("%d"), $3/$2*100}')
connections=$(ss -tun | wc -l)

echo "CPU: $cpu%"
echo "MEM: $mem%"
echo "Connections: $connections"

risk=0

if [ "$cpu" -gt 80 ]; then
echo "⚠ CPU anomaly detected"
risk=$((risk+20))
fi

if [ "$mem" -gt 80 ]; then
echo "⚠ Memory anomaly detected"
risk=$((risk+20))
fi

if [ "$connections" -gt 200 ]; then
echo "⚠ Network anomaly detected"
risk=$((risk+30))
fi

if [ "$risk" -gt 0 ]; then
echo "$(date) | ANOMALY_DETECTED score=$risk" >> "$EVENT_LOG"
fi

echo "Anomaly scan complete"
