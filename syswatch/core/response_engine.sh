#!/usr/bin/env bash

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVENT_LOG="$BASE_DIR/logs/events.log"

echo
echo "════ RESPONSE ENGINE ════"

# Block suspicious IPs
if command -v ufw >/dev/null 2>&1; then
    suspicious_ips=$(ss -tun | awk 'NR>1 {print $6}' | cut -d: -f1 | sort | uniq)

    for ip in $suspicious_ips
    do
        if [[ "$ip" != "127.0.0.1" && "$ip" != "::1" ]]; then
            echo "Blocking suspicious IP: $ip"
            sudo ufw deny from "$ip"
        fi
    done
fi

# Kill suspicious processes
suspicious=$(ps aux | grep -E "nc -l|bash -i|curl http|wget http" | grep -v grep)

if [ ! -z "$suspicious" ]; then
    echo "Suspicious process detected"

    pid=$(echo "$suspicious" | awk '{print $2}' | head -n1)

    echo "Terminating process $pid"
    kill -9 "$pid"

    echo "$(date) | PROCESS_TERMINATED $pid" >> "$EVENT_LOG"
fi

echo "Response cycle complete"
