#!/usr/bin/env bash

source core/logger.sh

alert_info() {
echo "[INFO] $1"
log_info "$1"
}

alert_warning() {
echo "[WARNING] $1"
log_warning "$1"
}

alert_critical() {
echo "[CRITICAL] $1"
log_critical "$1"
printf '\a'
}
