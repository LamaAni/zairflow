#!/usr/bin/env bash
: ${SCRIPTS_PATH:="$(dirname $(dirname $(realpath "$BASH_SOURCE[0]")))"}
source "$SCRIPTS_PATH/common.sh"

: "${IS_DRY_RUN:="false"}"
function out() {
    name="$1"
    shift
    value=("$@")
    log "output.$name = ${value[*]}"
    if [ $IS_DRY_RUN == "true" ]; then
        return 0
    fi
    echo "::set-output name=$name::${value[*]}"
}
