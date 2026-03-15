#!/usr/bin/env bash

THREAT_SCORE=0

add_score () {
    THREAT_SCORE=$((THREAT_SCORE + $1))
}

get_score () {
    echo $THREAT_SCORE
}

reset_score () {
    THREAT_SCORE=0
}

