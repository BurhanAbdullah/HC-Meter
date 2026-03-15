#!/usr/bin/env bash

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="$BASE_DIR/database/integrity.db"

echo
echo "════ BUILDING FILE INTEGRITY BASELINE ════"

find /etc /bin /usr/bin -type f 2>/dev/null | while read file
do
sha256sum "$file"
done > "$DB"

echo "Baseline created:"
echo "$DB"
