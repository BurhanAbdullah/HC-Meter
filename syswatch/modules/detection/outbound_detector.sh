#!/usr/bin/env bash

echo
echo "INTRUSION DETECTION — OUTBOUND TRAFFIC"

connections=$(ss -tun | grep -v 127.0.0.1 | wc -l)

if [ "$connections" -gt 50 ]; then
echo "[WARNING] High outbound traffic detected ($connections connections)"
else
echo "Outbound traffic normal"
fi
