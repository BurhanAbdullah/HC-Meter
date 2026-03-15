#!/usr/bin/env bash

echo
echo "AGENT — RESPONSE"

risk=$1

if [ "$risk" -gt 60 ]; then
echo "⚠ Defensive response triggered"
echo "Logging incident..."

date >> logs/incidents.log
echo "High risk detected" >> logs/incidents.log
fi#!/usr/bin/env bash

echo
echo "AGENT — RESPONSE"

risk=$1

if [ "$risk" -gt 60 ]; then
echo "⚠ Defensive response triggered"
echo "Logging incident..."

date >> logs/incidents.log
echo "High risk detected" >> logs/incidents.log
fi
