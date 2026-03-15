#!/usr/bin/env bash

echo
echo "════ THREAT INTELLIGENCE ENGINE ════"

THREAT_SCORE=0

# CPU check
cpu=$(top -bn1 | awk '/Cpu/ {print int($2+$4)}')

if [ "$cpu" -gt 90 ]; then
    THREAT_SCORE=$((THREAT_SCORE + 20))
fi

# Crypto miner detection
proc=$(ps aux | grep -E "xmrig|minerd|cryptominer" | grep -v grep | wc -l)

if [ "$proc" -gt 0 ]; then
    echo "⚠ Crypto miner detected"
    THREAT_SCORE=$((THREAT_SCORE + 40))
fi

# Reverse shell detection
rev=$(ps aux | grep -E "nc -l|bash -i|sh -i" | grep -v grep | wc -l)

if [ "$rev" -gt 0 ]; then
    echo "⚠ Possible reverse shell detected"
    THREAT_SCORE=$((THREAT_SCORE + 40))
fi

# Port exposure
ports=$(ss -tuln | wc -l)

if [ "$ports" -gt 30 ]; then
    THREAT_SCORE=$((THREAT_SCORE + 10))
fi

echo
echo "THREAT SCORE: $THREAT_SCORE"

if [ "$THREAT_SCORE" -lt 20 ]; then
LEVEL="LOW"
elif [ "$THREAT_SCORE" -lt 50 ]; then
LEVEL="MEDIUM"
elif [ "$THREAT_SCORE" -lt 80 ]; then
LEVEL="HIGH"
else
LEVEL="CRITICAL"
fi

echo "SYSTEM THREAT LEVEL: $LEVEL"
