#!/usr/bin/env bash

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo
echo "════════ SYSWATCH DAEMON ════════"
echo "Starting continuous monitoring..."
echo

while true
do

echo "Running security scan..."
bash "$BASE_DIR/core/engine.sh"

echo
echo "Next scan in 30 seconds"
echo

sleep 30

done
