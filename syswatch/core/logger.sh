#!/usr/bin/env bash

LOG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/logs"

log_event() {

TYPE=$1
MESSAGE=$2

echo "$(date '+%Y-%m-%d %H:%M:%S') [$TYPE] $MESSAGE" >> "$LOG_DIR/system.log"

}
