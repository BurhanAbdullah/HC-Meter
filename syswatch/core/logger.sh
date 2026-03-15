#!/usr/bin/env bash

LOG_FILE="logs/system.log"

log_info() {
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "$LOG_FILE"
}

log_warning() {
echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >> "$LOG_FILE"
}

log_critical() {
echo "$(date '+%Y-%m-%d %H:%M:%S') [CRITICAL] $1" >> "$LOG_FILE"
}
