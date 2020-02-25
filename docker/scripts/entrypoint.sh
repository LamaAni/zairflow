#!/usr/bin/env bash
CUR_PATH="$SCRIPTS_PATH"
: ${CUR_PATH:="$(realpath $(dirname $(realpath "$BASH_SOURCE[0]")))"}
: ${ZAIRFLOW_RUN_INITDB:="false"}

# shellcheck disable=SC1091
source "$CUR_PATH/common.sh"

# shellcheck disable=SC1091
source "$CUR_PATH/prepare_airflow_env.sh" || exit $?

function invoke_airflow() {
  # kill everything if failed.
  airflow "$@"
  assert $? "Failed: airflow $@" || exit $?
}

if [ "$ZAIRFLOW_RUN_INITDB" == "true" ]; then
  log:sep "Initializing airflow db.."
  invoke_airflow initdb
  assert $? "Failed to perform init db" || exit $?
else
  log:sep "Waiting for airflow db initialization"
  wait_for_airflow_db_ready
  assert $? "Airflow database was not initialized" || exit $?
fi

case "$ZAIRFLOW_CONTAINER_TYPE" in
worker)
  # a worker
  log:sep "Starting worker"
  invoke_airflow worker
  ;;
scheduler)
  log:sep "Starting scheduler"
  invoke_airflow scheduler
  ;;
webserver)
  log:sep "Starting webserver"
  invoke_airflow webserver
  ;;
flower)
  log:sep "Starting flower"
  invoke_airflow flower
  ;;
initdb)
  log:sep "Preparing the database"
  invoke_airflow initdb
  ;;
*)
  log:sep "Starting external command:"
  "$@"
  ;;
esac
