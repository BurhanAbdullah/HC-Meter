#!/usr/bin/env bash

echo
echo "════════ LOG INTRUSION MONITOR ════════"

fails=$(grep -i "failed password" /var/log/auth.log 2>/dev/null | wc -l)

if [ "$fails" -eq 0 ]; then
echo "✔ No login failures detected"
else
echo "⚠ $fails failed login attempts detected"
fi

echo
echo "Recent authentication activity:"
tail -n 5 /var/log/auth.log 2>/dev/null

