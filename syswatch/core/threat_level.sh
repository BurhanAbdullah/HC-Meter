#!/usr/bin/env bash

score=$1

echo
echo "════ THREAT LEVEL ════"

if [ "$score" -lt 20 ]; then
echo "LOW RISK ($score)"
elif [ "$score" -lt 50 ]; then
echo "MEDIUM RISK ($score)"
elif [ "$score" -lt 80 ]; then
echo "HIGH RISK ($score)"
else
echo "CRITICAL RISK ($score)"
fi
