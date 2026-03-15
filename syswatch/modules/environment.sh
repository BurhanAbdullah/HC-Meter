#!/usr/bin/env bash

echo
echo "════ ENVIRONMENT DETECTION ════"

if [ -f /.dockerenv ]; then
ENV="Docker Container"
elif grep -qa container /proc/1/cgroup 2>/dev/null; then
ENV="Container Environment"
else
ENV="Host System"
fi

echo "Environment: $ENV"
echo "Kernel: $(uname -r)"
echo "OS: $(uname -s)"
echo "Architecture: $(uname -m)"
echo "Hostname: $(hostname)"
