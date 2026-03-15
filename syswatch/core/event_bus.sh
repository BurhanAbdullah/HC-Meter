#!/usr/bin/env bash

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVENT_LOG="$BASE_DIR/logs/events.log"

mkdir -p "$BASE_DIR/logs"

publish_event() {

event="$1"
timestamp=$(date +"%Y-%m-%d %H:%M:%S")

echo "$timestamp | $event" >> "$EVENT_LOG"

}
