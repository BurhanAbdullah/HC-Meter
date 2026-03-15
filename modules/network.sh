#!/usr/bin/env bash

echo
echo "════════ NETWORK MONITOR ════════"

echo
echo "Listening Ports"
ss -tuln | head

echo
echo "External Connections"
ss -tunap | grep -v 127.0.0.1 | head
