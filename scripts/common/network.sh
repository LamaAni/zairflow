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

function wait_for_resource_connections() {
  local resource_connections=($ZAIRFLOW_WAIT_FOR)
  if [ "${#resource_connections[@]}" -ne 0 ]; then
    log:sep "Checking url resource connections"
    for wait_for_url in "${resource_connections[@]}"; do
      log:info "Waiting for $wait_for_url to be ready..."
      wait_for_connection "$wait_for_url" || return $?
      assert $? "Failed connecting to $wait_for_url"
    done
  fi
}
