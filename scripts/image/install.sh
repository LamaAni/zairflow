#!/usr/bin/env bash
: "${SCRIPTS_PATH:="$(dirname "$(dirname "$(realpath "${BASH_SOURCE[0]}")")")"}"
: "${GIT_AUTOSYNC_VERSION:="latest"}"
: "${ZBASH_COMMONS_VERSION="latest"}"

echo "Verifying zbash commons install..."
curl -Ls "https://raw.githubusercontent.com/LamaAni/zbash-commons/master/install?ts_$(date +%s)=read" |
    bash -s $ZBASH_COMMONS_VERSION || exit $?
source "$SCRIPTS_PATH/common.sh" || exit $?

log:sep "Installing git_autosync"
curl -Ls "https://raw.githubusercontent.com/LamaAni/git_autosync/master/install?ts_$(date +%s)=$RANDOM" | bash
