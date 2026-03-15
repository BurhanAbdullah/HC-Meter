#!/usr/bin/env bash

echo
echo "════════ NETWORK MONITOR ════════"

echo
echo "Listening Ports"

ss -tuln | awk 'NR>1 {print $5}' | sed 's/.*://' | sort -n | uniq

echo
echo "External Connections"

ss -tunap | grep -v 127.0.0.1 | head
