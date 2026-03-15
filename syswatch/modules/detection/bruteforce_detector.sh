#!/usr/bin/env bash

echo
echo "INTRUSION DETECTION — BRUTE FORCE"

LOG="/var/log/auth.log"

if [ -f "$LOG" ]; then

fails=$(grep "Failed password" "$LOG" | wc -l)

if [ "$fails" -gt 10 ]; then
echo "[CRITICAL] Possible brute force attack ($fails attempts)"
else
echo "No brute force activity detected"
fi

else
echo "Auth log unavailable (container environment)"
fi
