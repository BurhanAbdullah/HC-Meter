#!/usr/bin/env bash

cpu=$(top -bn1 | awk '/Cpu/ {print int($2+$4)}')
mem=$(free | awk '/Mem/ {printf("%.0f"), $3/$2*100}')
disk=$(df / | awk 'NR==2 {print $5}' | tr -d '%')

bar () {
v=$1
f=$((v/5))
e=$((20-f))

printf "["
printf "%0.s█" $(seq 1 $f)
printf "%0.s░" $(seq 1 $e)
printf "] %s%%\n" "$v"
}

echo
echo "╔════════════════ SYSWATCH DASHBOARD ════════════════╗"

echo
echo "CPU"
bar "$cpu"

echo "MEMORY"
bar "$mem"

echo "DISK"
bar "$disk"

# -----------------------------
# Risk scoring
# -----------------------------

risk=0

if [ "$cpu" -gt 80 ]; then
risk=$((risk+30))
fi

if [ "$mem" -gt 80 ]; then
risk=$((risk+30))
fi

if [ "$disk" -gt 80 ]; then
risk=$((risk+20))
fi

echo
echo "SYSTEM RISK LEVEL"

if [ "$risk" -lt 30 ]; then
echo "✔ LOW RISK ($risk)"
elif [ "$risk" -lt 60 ]; then
echo "⚠ MEDIUM RISK ($risk)"
else
echo "✖ HIGH RISK ($risk)"
fi

echo
echo "Top CPU Processes"
ps -eo pid,comm,%cpu --sort=-%cpu | head -n 6
