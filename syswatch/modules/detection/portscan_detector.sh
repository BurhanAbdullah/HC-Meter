#!/usr/bin/env bash

echo
echo "INTRUSION DETECTION — PORT SCAN"

connections=$(ss -tan | wc -l)

if [ "$connections" -gt 200 ]; then
echo "[WARNING] Possible port scanning activity"
echo "Active connections: $connections"
else
echo "Connection count normal"
fi
