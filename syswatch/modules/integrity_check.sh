#!/usr/bin/env bash

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="$BASE_DIR/database/integrity.db"

echo
echo "════ FILE INTEGRITY CHECK ════"

if [ ! -f "$DB" ]; then
echo "No baseline found. Run integrity_baseline first."
exit
fi

while read hash file
do
current=$(sha256sum "$file" 2>/dev/null | awk '{print $1}')

if [ "$hash" != "$current" ]; then
echo "⚠ ALERT: File modified -> $file"
fi

done < "$DB"

echo "Integrity scan complete."
