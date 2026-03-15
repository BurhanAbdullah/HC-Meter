#!/usr/bin/env bash

echo
echo "════════ FILE INTEGRITY MONITOR ════════"

echo
echo "Files modified in last 24 hours:"
find /tmp -type f -mtime -1 2>/dev/null | head

echo
echo "World-writable files:"
find / -type f -perm -002 2>/dev/null | head
