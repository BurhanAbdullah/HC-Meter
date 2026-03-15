#!/usr/bin/env bash

echo
echo "AGENT — ANALYZER"

cpu=$1
mem=$2
connections=$3

risk=0

if [ "$cpu" -gt 80 ]; then
risk=$((risk+20))
fi

if [ "$mem" -gt 80 ]; then
risk=$((risk+20))
fi

if [ "$connections" -gt 200 ]; then
risk=$((risk+30))
fi

echo "$risk"
