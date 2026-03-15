#!/usr/bin/env bash

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVENT_LOG="$BASE_DIR/logs/events.log"

echo
echo "════ THREAT INTELLIGENCE ENGINE ════"

# Extract external IP connections
ips=$(ss -tun | awk 'NR>1 {print $6}' | cut -d: -f1 | sort | uniq)

for ip in $ips
do

# Skip local addresses
if [[ "$ip" == "127.0.0.1" ]] || [[ "$ip" == "::1" ]]; then
continue
fi

# Simple reputation check using ipinfo
rep=$(curl -s "https://ipinfo.io/$ip" | grep -i "bogon")

if [ ! -z "$rep" ]; then
echo "⚠ Suspicious IP detected: $ip"

echo "$(date) | MALICIOUS_IP $ip" >> "$EVENT_LOG"
fi

done

echo "Threat intelligence scan complete"
