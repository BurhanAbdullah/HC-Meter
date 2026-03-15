#!/usr/bin/env bash

echo
echo "════════ OUTBOUND TRAFFIC MONITOR ════════"

connections=$(ss -tun | grep -v "127.0.0.1" | wc -l)

if [ "$connections" -gt 50 ]; then
echo "⚠ Unusual outbound traffic detected"
echo "Connections: $connections"
printf '\a'
else
echo "✔ Outbound traffic normal"
fi
