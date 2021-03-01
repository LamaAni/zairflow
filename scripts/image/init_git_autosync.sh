#!/usr/bin/env bash
: ${SCRIPTS_PATH:="$(dirname $(dirname $(realpath "$BASH_SOURCE[0]")))"}
# shellcheck disable=SC1091
source "$SCRIPTS_PATH/common.sh"

# Config
: "${GIT_AUTOSYNC_REPO_LOCAL_PATH="/app"}"
: "${GIT_AUTOSYNC_CLEAR_DIRECTORY="true"}"

function init_git_autosync() {
    if [ "$GIT_AUTOSYNC_CLEAR_DIRECTORY" == "true" ]; then
        log "Cleaning git autosync directory @ $GIT_AUTOSYNC_REPO_LOCAL_PATH"
        local to_be_deleted=($(find "$GIT_AUTOSYNC_REPO_LOCAL_PATH" -maxdepth 1))
        for p in "${to_be_deleted[@]}"; do
            if [ "$p" == "$GIT_AUTOSYNC_REPO_LOCAL_PATH" ]; then continue; fi
            log "Removing: $p"
            rm -rf "$p"
            assert $? "Failed to clean directory before git autosync @ $p" || return $?
        done
        ls "$GIT_AUTOSYNC_REPO_LOCAL_PATH"
    fi

    # running git_autosync asynchronically.
    git_autosync --async
}

init_git_autosync "$@"
