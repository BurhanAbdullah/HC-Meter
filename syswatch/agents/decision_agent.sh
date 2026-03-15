#!/usr/bin/env bash

echo
echo "AGENT — DECISION"

risk=$1

if [ "$risk" -lt 20 ]; then
level="LOW"
elif [ "$risk" -lt 50 ]; then
level="MEDIUM"
elif [ "$risk" -lt 80 ]; then
level="HIGH"
else
level="CRITICAL"
fi

echo "Threat Level: $level"
source "$(dirname "$0")/../core/event_bus.sh"

publish_event "THREAT_LEVEL_$level"
