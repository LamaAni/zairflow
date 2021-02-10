#!/usr/bin/env bash
: ${SCRIPTS_PATH:="$(dirname $(dirname $(realpath "$BASH_SOURCE[0]")))"}
# shellcheck disable=SC1091
source "$SCRIPTS_PATH/common.sh"

log:sep "Installing git_autosync"

: "${GIT_AUTOSYNC_VERSION:="latest"}"

curl -Ls "https://raw.githubusercontent.com/LamaAni/git_autosync/master/install?ts_$(date +%s)=$RANDOM" | bash

log:sep "Configuring airflow command overrids.. (KubernetesExecutor)"
mv /usr/local/bin/airflow /usr/local/bin/call_airflow &&
    ln -sf /scripts/image/invoke_airflow /usr/local/bin/airflow
assert $? "Failed to configure airflow kubernetes override." || exit $?
