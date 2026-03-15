#!/usr/bin/env bash

alert() {

LEVEL=$1
MESSAGE=$2

case $LEVEL in
INFO)
echo "[INFO] $MESSAGE"
;;

WARNING)
echo "[WARNING] $MESSAGE"
;;

CRITICAL)
echo "[CRITICAL] $MESSAGE"
printf '\a'
;;

esac

}

