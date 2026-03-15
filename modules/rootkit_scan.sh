#!/usr/bin/env bash

echo
echo "════════ ROOTKIT / BINARY SCAN ════════"

sus=$(find /tmp /dev /var/tmp -type f -executable 2>/dev/null | head)

if [ -z "$sus" ]; then
echo "✔ No suspicious binaries found"
else
echo "⚠ Suspicious executables:"
echo "$sus"
fi
