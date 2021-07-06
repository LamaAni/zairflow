#!/bin/bash

# methods for general purpose use.
: "${ZARIFLOW_CONNECTION_WAIT_TRIES:="60"}"
: "${ZARIFLOW_CONNECTION_WAIT_TIMEOUT:="1"}"
: "${ZARIFLOW_CONNECTION_WAIT_INTERVAL:="1"}"

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

: "${ZARIFLOW_DB_WAIT_TRIES:="60"}"
: "${ZARIFLOW_DB_WAIT_INTERVAL:="1"}"

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
