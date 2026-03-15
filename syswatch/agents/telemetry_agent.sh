#!/usr/bin/env bash

SERVER="http://localhost:9000/telemetry"

cpu=$(top -bn1 | grep "Cpu(s)" | awk '{print int($2)}')
mem=$(free | awk '/Mem:/ {printf("%d"), $3/$2*100}')
con=$(ss -tuln | wc -l)

json=$(printf '{"cpu":%s,"memory":%s,"connections":%s}' "$cpu" "$mem" "$con")

curl -s -X POST $SERVER \
-H "Content-Type: application/json" \
-d "$json"
