#!/usr/bin/env bash
: ${SCRIPTS_PATH:="$(dirname $(dirname $(realpath "$BASH_SOURCE[0]")))"}
# shellcheck disable=SC1091
source "$SCRIPTS_PATH/common.sh"

# Config
: ${ZAIRFLOW_GIT_AUTOSYNC_PATH="/app"}
: ${ZAIRFLOW_GIT_AUTOSYNC_CLEAR_DIRECTORY="true"}

function init_git_autosync() {
    local uri="$1"
    local sync_path="$2"
    local branch="$3"
    local clear_target_directory="$ZAIRFLOW_GIT_AUTOSYNC_CLEAR_DIRECTORY"

    : ${uri:="$ZAIRFLOW_GIT_AUTOSYNC_URI"}
    : ${sync_path:="$ZAIRFLOW_GIT_AUTOSYNC_PATH"}
    : ${branch:="$ZAIRFLOW_GIT_AUTOSYNC_BRANCH"}

    [ -n "$uri" ]
    assert $? "The git repo url must be defined (if the repo already exists use 'internal')"

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

    if [ -n "$branch" ]; then
        local branch_arg="--branch ${branch}"
    fi

    function clone_using_tempdir() {
        local tmp_clone_dir=""
        log:info "Creating an initial clone in a temp directory @ $tmp_clone_dir ..."
        tmp_clone_dir="$(mktemp -d)"
        git clone --single-branch $branch_arg "$uri" "$tmp_clone_dir"
        assert $? "Failed to clone git repo." || revert_path $? || return $?
        log:info "Copying repo to working directory @ $PWD"
        cp -afr $tmp_clone_dir/. .
        assert $? "Failed to copy cloned git repo." || revert_path $? || return $?
    }

    function delete_source_and_clone() {
        log:info "Deleting existing source files in $PWD..."
        rm -rf ..?* .[!.]* *
        assert $? "Failed to delete all files from source directory." || return $?

        log:info "Cloning repo "
        git clone --single-branch $branch_arg "$uri" .
        assert $? "Failed to clone git repo." || revert_path $? || return $?
    }

    if [ "$uri" != "internal" ]; then
        log:info "Initializing repo @ $PWD, cloaing from remote..."

        if [ "$clear_target_directory" == "true" ]; then
            delete_source_and_clone || return $?
        else
            clone_using_tempdir || return $?
        fi
        log:info "Validating repo"
        git status &>/dev/null
        assert $? "Failed to assert git repo creation." || revert_path $? || return $?
        log:info "Git repo initialized succesfully"
    fi

    git_autosync --async
    assert $? "Failed to start git autosync" || revert_path $? || return $?

    revert_path || return $?
}

init_git_autosync "$@"
