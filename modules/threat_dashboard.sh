#!/usr/bin/env bash

echo
echo "════════ THREAT DASHBOARD ════════"

events=$(tail -n 5 logs/intrusions.log 2>/dev/null)

if [ -z "$events" ]; then
echo "✔ No recent security events"
else
echo "Recent security alerts:"
echo "$events"
fi
