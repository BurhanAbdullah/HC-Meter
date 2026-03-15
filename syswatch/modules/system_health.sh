#!/usr/bin/env bash

echo
echo "SYSTEM HEALTH"

cpu=$(top -bn1 | awk '/Cpu/ {print int($2+$4)}')
mem=$(free | awk '/Mem/ {printf("%.0f"), $3/$2*100}')
disk=$(df / | awk 'NR==2 {print $5}')

echo "CPU: $cpu%"
echo "MEM: $mem%"
echo "DISK: $disk"
