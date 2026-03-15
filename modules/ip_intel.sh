#!/usr/bin/env bash

echo
echo "════════ ATTACKER INTELLIGENCE ════════"

ip=$(grep "Failed password" /var/log/auth.log 2>/dev/null | tail -1 | awk '{print $11}')

if [ -z "$ip" ]; then
echo "✔ No attacker IP detected"
else

echo "Attacker IP: $ip"
echo

curl -s ipinfo.io/$ip | head

fi
