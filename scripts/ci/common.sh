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

function split_versions() {
    local sep="$1"
    shift
    local versions=""
    local parsed_versions=""
    versions=("$@")
    parsed_versions=()

    for ver in "${versions[@]}"; do
        local version_split
        IFS="$sep" read -ra version_split <<<"$ver"

        local partial_version=""
        local is_first_split=1

        for part in "${version_split[@]}"; do
            partial_version="${partial_version}${part}"
            if [ $is_first_split -eq 1 ] && [ "${#version_split[@]}" -gt 1 ]; then
                is_first_split=0
            else
                parsed_versions+=("$partial_version")
            fi
            partial_version="${partial_version}$sep"
        done
    done
    IFS=" " echo "${parsed_versions[@]}"
}
