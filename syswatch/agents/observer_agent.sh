#!/usr/bin/env bash

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo
echo "AGENT — OBSERVER"

cpu=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d. -f1)
mem=$(free | awk '/Mem:/ {printf("%d"), $3/$2*100}')

connections=$(ss -tun | wc -l)

echo "CPU:$cpu"
echo "MEM:$mem"
echo "CONNECTIONS:$connections"
