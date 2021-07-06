#!/usr/bin/env bash
type zbash_commons &>/dev/null
if [ "$?" -ne 0 ]; then
  echo "[DOWNLOAD] Downloading zbash_commons from latest release.."
  ZBASH_COMMONS_GET_SCRIPT="$(curl -Ls "https://raw.githubusercontent.com/LamaAni/zbash-commons/master/get?ts_$(date +%s)=$RANDOM")"
  ZBASH_COMMONS="$(bash -c "$ZBASH_COMMONS_GET_SCRIPT")"
  eval "$ZBASH_COMMONS"
else
  source zbash_commons
fi

SCRIPTS_PATH="$SCRIPTS_PATH"
: "${SCRIPTS_PATH:="$(realpath $(dirname $(realpath "$BASH_SOURCE[0]")))"}"
: "${ZAIRFLOW_RUN_INITDB:="false"}"

function load_scripts() {
  for file in $SCRIPTS_PATH/common/*; do
    source "$file"
    assert $? "Error while loading lib file: $file" || return $?
  done
}

load_scripts
assert $? "Faild to load zairflow core scripts" || exit $?
