#!/usr/bin/env bash
CUR_PATH="$SCRIPTS_PATH"
: ${CUR_PATH:="$(realpath $(dirname $(realpath "$BASH_SOURCE[0]")))"}
source "$CUR_PATH/common.sh"

function init_git_autosync() {
    local uri="$1"
    local sync_path="$2"

    [ -n "$uri" ]
    assert $? "The git repo url must be defined (if the repo already exists use 'internal')"

    log:info "Preparing git auto-sync"
    [ -n "$sync_path" ]
    assert $? "The sync path must be defined." || return $?

    local cur_path="$PWD"

    function revert_path() {
        log:info "Reverting to calling path @ $cur_path"
        cd "$cur_path"
        assert $? "Could not return to original path" || return $?
        return "$@"
    }

    log:info "Moving into repo path @ $sync_path"
    cd "$sync_path"
    assert $? "Could not enter sync path, or path dose not exist" || return $?

    log:info "Initializing repo"
    git status &>/dev/null
    if [ $? -ne 0 ]; then
        log:warn "Git repo not found @ $PWD, attempting to clone $uri..."
        git clone "$uri" .
        assert $? "Failed to initialize git repo." || revert_path $? || return $?
    fi

    git_autosync --async
    assert $? "Failed to start git autosync" || revert_path $? || return $?

    revert_path || return $?
}

init_git_autosync "$@"
