#!/usr/bin/env bash

SCRIPTS_PATH="$SCRIPTS_PATH"
: ${SCRIPTS_PATH:="$(realpath $(dirname $(realpath "$BASH_SOURCE[0]")))"}
: ${ZAIRFLOW_RUN_INITDB:="false"}

source zbash_commons || echo "zbash_commons not found. See https://github.com/LamaAni/zbash-commons for install instructions" && exit 1

####################################
# Logger

export red=$'\e[1;31m'
export green=$'\e[1;32m'
export yellow=$'\e[1;33m'
export blue=$'\e[1;34m'
export magenta=$'\e[1;35m'
export cyan=$'\e[1;36m'
export light_blue=$'\e[0;94m'
export deep_green=$'\e[0;32m'
export dark_magenta=$'\e[0;35m'
export light_=$'\e[1;31m'
export end_color=$'\e[0m'
export ec="$end_color"

function paint() {
  local color="$1"
  local text="$2"
  echo "${!color}${text}${ec}"
}

export LINE_SEPARATOR='------------------------------------'

function log_core() {
  local prefex="$1"
  shift
  echo "$prefex: " "$@"
}

function assert() {
  local err="$1"
  : ${err:=0}
  if [ "$err" -ne 0 ]; then
    log_core "${red}ERROR${end_color}" "$2" >>/dev/stderr
    return $err
  fi
}

function assert_warning() {
  local err="$1"
  : ${err:=0}
  if [ "$err" -ne 0 ]; then
    log_core "${yellow}WARNING${end_color}" "$2" >>/dev/stderr
    return $err
  fi
}

function log:info() {
  log_core "${green}INFO${end_color}" "$@"
}

function log:warn() {
  log_core "${yellow}WARNING${end_color}" "$@"
}

function log:error() {
  log_core "${red}ERROR${end_color}" "$@"
}

function log:trace() {
  log_core "${magenta}TRACE${end_color}" "$@"
}

function log() {
  log:info "$@"
}

function log:warning() {
  log:warn "$@"
}

function log:sep() {
  echo "$green$LINE_SEPARATOR$end_color"
  if [ "$#" -gt 0 ]; then
    log_core "${magenta}->${end_color}" "$@"
  fi
}

#########################################
# Common methods

# usage: value_in_array [val] [ar1] [ar2] ...
function value_in_array() {
  local val=$1
  shift
  while [ $# -gt 0 ]; do
    if [ "$1" = "$val" ]; then
      return 1
    fi
    shift
  done
  return 0
}

########################################
# Airflow

function get_airflow_config_vals() {
  python3 $SCRIPTS_PATH/image/get_airflow_config_vals.py "$@"
}

########################################
# Connection

# methods for general purpose use.
: ${ZARIFLOW_CONNECTION_WAIT_TRIES:="60"}
: ${ZARIFLOW_CONNECTION_WAIT_TIMEOUT:="1"}
: ${ZARIFLOW_CONNECTION_WAIT_INTERVAL:="1"}

function wait_for_connection() {
  local host=$1
  local port=$2

  if [ -z "$port" ]; then
    local uri_parts
    uri_parts=($(echo "$host" | sed -e "s/:/ /g"))
    host="${uri_parts[0]}"
    port="${uri_parts[1]}"
  fi

  [ -n "$port" ]
  assert $? "wait_for_connection: You must provide a port" || return $?
  [ -n "$host" ]
  assert $? "wait_for_connection: You must provide a host" || return $?

  log:info "Checking $host:$port is open with an interval of $ZARIFLOW_CONNECTION_WAIT_INTERVAL, max $ZARIFLOW_CONNECTION_WAIT_TRIES times.."
  WAIT_INDEX=0
  while true; do
    nc -w $ZARIFLOW_CONNECTION_WAIT_TIMEOUT -zv "$host" "$port" &>/dev/null
    if [ $? -ne 0 ]; then
      if [ $WAIT_INDEX -gt $ZARIFLOW_CONNECTION_WAIT_TRIES ]; then
        log:error "Timed out while waiting for port $port on $host"
        return 3
      fi
      log:info "Attempt $WAIT_INDEX/$ZARIFLOW_CONNECTION_WAIT_TRIES, port $port not available on $host, retry in $ZARIFLOW_CONNECTION_WAIT_INTERVAL"
    else
      log:info "Port $port is open on $host"
      break
    fi
    WAIT_INDEX=$((WAIT_INDEX + 1))
    sleep "$ZARIFLOW_CONNECTION_WAIT_INTERVAL"
  done
}

: ${ZARIFLOW_DB_WAIT_TRIES:="60"}
: ${ZARIFLOW_DB_WAIT_INTERVAL:="1"}

function wait_for_airflow_db_ready() {
  local count=0

  while true; do
    last_print=$(python3 "$SCRIPTS_PATH/image/check_airflow_db.py" 2>&1)
    last_error=$?
    if [ $last_error -eq 0 ]; then
      printf "%s\n" "$last_print"
      break
    fi
    count=$((count + 1))
    if [ "$count" -ge "$ZARIFLOW_DB_WAIT_TRIES" ]; then
      assert $last_error "$last_print"$'\n'"Timed out while waiting for db to initialize." || return $?
    fi
    log:info "Airflow db not ready ($count/$ZARIFLOW_DB_WAIT_TRIES), retry in $ZARIFLOW_DB_WAIT_INTERVAL [s].."
    sleep "$ZARIFLOW_DB_WAIT_INTERVAL"
  done
}

function join_by() {
  local IFS="$1"
  shift
  echo "$*"
}
