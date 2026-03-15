#!/usr/bin/env bash

echo
echo "════════ PROCESS THREAT SCAN ════════"

sus=$(ps aux | grep -Ei "xmrig|minerd|cryptominer|nc -l|bash -i|/dev/tcp" | grep -v grep)

if [ -z "$sus" ]; then
echo "✔ No suspicious processes detected"
else
echo "⚠ Suspicious processes detected:"
echo "$sus"
fi
