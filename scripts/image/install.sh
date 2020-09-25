#!/usr/bin/env bash
: ${SCRIPTS_PATH:="$(dirname $(dirname $(realpath "$BASH_SOURCE[0]")))"}
# shellcheck disable=SC1091
source "$SCRIPTS_PATH/common.sh"

log:sep "Installing git_autosync"

git clone "https://github.com/LamaAni/git_autosync.git" --branch "$GIT_AUTOSYNC_BRANCH" /scripts/git_autosync &&
    ln -sf /scripts/git_autosync/git_autosync /usr/bin/git_autosync &&
    chmod +x -R /scripts && chmod +x /usr/bin/git_autosync
assert $? "Failed to install git_autosync" || exit $?

log:sep "Configuring airflow command overrids.. (KubernetesExecutor)"
mv /usr/local/bin/airflow /usr/local/bin/call_airflow &&
    ln -sf /scripts/image/invoke_airflow /usr/local/bin/airflow
assert $? "Failed to configure airflow kubernetes override." || exit $?
