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
