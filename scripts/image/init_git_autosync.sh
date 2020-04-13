#!/usr/bin/env bash
: ${SCRIPTS_PATH:="$(dirname $(dirname $(realpath "$BASH_SOURCE[0]")))"}
# shellcheck disable=SC1091
source "$SCRIPTS_PATH/common.sh"

function init_git_autosync() {
    local uri="$1"
    local sync_path="$2"
    local branch="$3"

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

    if [ "$uri" != "internal" ]; then
        if [ -n "$branch" ]; then
            local branch_arg="--branch ${branch}"
        fi
        log:info "Initializing repo"
        git status &>/dev/null
        if [ $? -ne 0 ]; then
            # log:warn "Git repo not found @ $PWD, attempting to clone $uri..."
            local tmp_clone_dir=""
            tmp_clone_dir="$(mktemp -d)"
            log:info "Git repo not found @ $PWD. Creating an initial clone in a temp directory @ $tmp_clone_dir ..."
            git clone --single-branch $branch_arg "$uri" "$tmp_clone_dir"
            assert $? "Failed to initialize git repo." || revert_path $? || return $?
            log:info "Copying repo to working directory @ $PWD"
            cp -afr $tmp_clone_dir/. .
            assert $? "Failed to copy cloned git repo." || revert_path $? || return $?
            log:info "Validating git repo @ $PWD"
            git status &>/dev/null
            [ $? -eq 0 ]
            assert $? "Failed to assert git repo creation." || revert_path $? || return $?
            log:info "Autosync clone OK."
        fi
    fi

    git_autosync --async
    assert $? "Failed to start git autosync" || revert_path $? || return $?

    revert_path || return $?
}

init_git_autosync "$@"
