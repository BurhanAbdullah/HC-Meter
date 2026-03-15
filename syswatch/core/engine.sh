#!/usr/bin/env bash

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo
echo "SYSWATCH Engine Starting"

for module in "$BASE_DIR/modules/"*.sh
do
    if [ -x "$module" ]; then
        bash "$module"
    fi
done

echo
echo "All modules executed"
for module in "$BASE_DIR/modules/detection/"*.sh
do
    if [ -x "$module" ]; then
        bash "$module"
    fi
done
bash "$BASE_DIR/core/threat_engine.sh"
echo
echo "===== AGENT SYSTEM ====="

obs=$(bash agents/observer_agent.sh)

cpu=$(echo "$obs" | grep CPU | cut -d: -f2)
mem=$(echo "$obs" | grep MEM | cut -d: -f2)
con=$(echo "$obs" | grep CONNECTIONS | cut -d: -f2)

cpu=${cpu:-0}
mem=${mem:-0}
con=${con:-0}

risk=$(bash agents/analyzer_agent.sh "$cpu" "$mem" "$con")

bash agents/decision_agent.sh "$risk"
bash agents/response_agent.sh "$risk"
echo
echo "════ ACTIVE DEFENSE ════"
bash "$BASE_DIR/core/response_engine.sh"

echo
echo "════ THREAT INTELLIGENCE ════"
bash "$BASE_DIR/core/threat_intel.sh"
echo
echo "════ ANOMALY DETECTION ════"
bash "$BASE_DIR/modules/anomaly_detector.sh"
