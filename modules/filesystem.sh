#!/usr/bin/env bash

echo
echo "════════ FILE INTEGRITY CHECK ════════"

echo
echo "Recently modified files (24h)"

find /tmp -type f -mtime -1 2>/dev/null | head

echo
echo "World-writable files"

find / -type f -perm -002 2>/dev/null | head
