#!/usr/bin/env bash

LOGFILE="$BASE_DIR/logs/intrusions.log"

echo
echo "════════ REAL-TIME THREAT MONITOR ════════"

# detect brute force attempts
fails=$(grep -i "failed password" /var/log/auth.log 2>/dev/null | wc -l)

if [ "$fails" -gt 5 ]; then
echo "⚠ BRUTE FORCE ATTACK DETECTED"

ip=$(grep "Failed password" /var/log/auth.log | tail -1 | awk '{print $11}')

echo "Attacker IP: $ip"

echo "$(date) brute force from $ip" >> "$LOGFILE"

echo "Checking attacker location..."

curl -s ipinfo.io/$ip | head

fi
