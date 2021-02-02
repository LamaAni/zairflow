#!/usr/bin/env bash

SCRIPTS_PATH="$SCRIPTS_PATH"
: ${SCRIPTS_PATH:="$(realpath $(dirname $(realpath "$BASH_SOURCE[0]")))"}
: ${ZAIRFLOW_RUN_INITDB:="false"}

source zbash_commons
if [ $? -ne 0 ]; then
  echo "zbash_commons not found. Please see: https://github.com/LamaAni/zbash-commons"
fi

function load_scripts() {
  for file in $SCRIPTS_PATH/common/*; do
    source "$file"
    assert $? "Error while loading lib file: $file" || return $?
  done
}

load_scripts || exist $?
