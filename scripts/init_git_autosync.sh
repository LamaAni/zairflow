#!/usr/bin/env bash
CUR_PATH="$SCRIPTS_PATH"
: ${CUR_PATH:="$(realpath $(dirname $(realpath "$BASH_SOURCE[0]")))"}
source "$CUR_PATH/common.sh"

function validate_git_repo() {
    git status "$@" &>/dev/null
    if [ $? -ne 0 ]; then
        log::warn "Not 'native' git repository found"
        return 1
    fi
    return 0
}

function init_git_autosync() {
    local uri="$1"
    local sync_path="$2"
    local dags_subpath="$3"

    : ${dags_subpath:=""}

    [ -n "$uri" ]
    assert $? "The git repo url must be defined (if the repo already exists use 'internal')"

    log:sep "Preparing git auto-sync"
    [ -n "$sync_path" ]
    assert $? "The sync path must be defined." || return $?

    local cur_path="$PWD"

    function revert_path() {
        cd "$cur_path"
        assert $? "Could not return to original path" || return $?
        return "$@"
    }

    cd "$sync_path"
    assert $? "Could not enter sync path, or path dose not exist" || return $?

    validate_git_repo || git clone "$uri" "$sync_path"
    assert $? "Failed to initialize git repo." || revert_path $? || return $?

    git_autosync --async
    assert $? "Failed to start git autosync" || revert_path $? || return $?

    revert_path || return $?
}

init_git_autosync "$@"
