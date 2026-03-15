#!/usr/bin/env bash

echo
echo "════════ ATTACKER BLOCKER ════════"

fail_count=$(grep -i "failed password" /var/log/auth.log 2>/dev/null | wc -l)

if [ "$fail_count" -gt 10 ]; then

ip=$(grep "Failed password" /var/log/auth.log | tail -1 | awk '{print $11}')

echo "⚠ Brute-force attack detected"
echo "Attacker IP: $ip"

if command -v ufw >/dev/null; then
sudo ufw deny "$ip"
echo "✔ IP blocked using UFW"
else
echo "⚠ Firewall not installed (UFW)"
fi

echo "$(date) blocked $ip" >> logs/intrusions.log

else

echo "✔ No brute-force attack detected"

fi

