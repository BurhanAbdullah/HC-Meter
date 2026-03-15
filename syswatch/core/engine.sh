#!/usr/bin/env bash

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

source "$BASE_DIR/core/threat_score.sh"

reset_score

echo
echo "════ SYSWATCH ENGINE ════"

for module in "$BASE_DIR/modules/"*.sh
do
    if [ -x "$module" ]; then
        bash "$module"
    fi
done

score=$(get_score)

bash "$BASE_DIR/core/threat_level.sh" "$score"

echo
echo "Modules complete."
