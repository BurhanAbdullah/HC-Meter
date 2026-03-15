#!/usr/bin/env bash

echo
echo "════════ PORT SCAN DETECTOR ════════"

connections=$(ss -tn state established | wc -l)

if [ "$connections" -gt 150 ]; then
echo "⚠ Possible port scanning activity detected"
echo "Active connections: $connections"
printf '\a'

echo "$(date) possible port scan detected ($connections connections)" >> logs/intrusions.log

else
echo "✔ Network activity normal"
fi
