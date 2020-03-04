#!/usr/bin/env bash
CUR_PATH="$SCRIPTS_PATH"
: ${CUR_PATH:="$(realpath $(dirname $(realpath "$BASH_SOURCE[0]")))"}
: ${ZAIRFLOW_RUN_INITDB:="false"}

# shellcheck disable=SC1091
source "$CUR_PATH/common.sh"

if [ -n "$ZAIRFLOW_ENTRYPOINT_INIT_HOOK" ]; then
  log:sep "Starting init hook: $ZAIRFLOW_ENTRYPOINT_INIT_HOOK"
  "$ZAIRFLOW_ENTRYPOINT_INIT_HOOK"
  assert $? "Failed to exec init hook" || exit $?
fi

# shellcheck disable=SC1091
source "$CUR_PATH/prepare_airflow_env.sh" || exit $?

function invoke_airflow() {
  # kill everything if failed.
  airflow "$@"
  assert $? "Failed: airflow $@" || exit $?
}

function check_for_db() {
  if [ "$ZAIRFLOW_RUN_INITDB" == "true" ]; then
    log:sep "Initializing airflow db.."
    invoke_airflow initdb
    assert $? "Failed to perform init db" || return $?
  else
    log:sep "Waiting for airflow db initialization"
    wait_for_airflow_db_ready
    assert $? "Airflow database was not initialized" || return $?
  fi
}

function check_for_run_hooks() {
  if [ -n "$ZAIRFLOW_ENTRYPOINT_RUN_HOOK" ]; then
    log:sep "Starting run hook: $ZAIRFLOW_ENTRYPOINT_RUN_HOOK"
    "$ZAIRFLOW_ENTRYPOINT_RUN_HOOK"
    assert $? "Failed to exec run hook" || exit $?
  fi
}

case "$ZAIRFLOW_CONTAINER_TYPE" in
worker)
  # a worker
  log:sep "Starting worker"
  check_for_db || exit $?
  check_for_run_hooks || exit $?
  invoke_airflow worker
  ;;
scheduler)
  log:sep "Starting scheduler"
  check_for_db || exit $?
  check_for_run_hooks || exit $?
  invoke_airflow scheduler
  ;;
webserver)
  log:sep "Starting webserver"
  check_for_db || exit $?
  check_for_run_hooks || exit $?
  invoke_airflow webserver
  ;;
flower)
  log:sep "Starting flower"
  check_for_run_hooks || exit $?
  invoke_airflow flower
  ;;
initdb)
  log:sep "Preparing the database"
  invoke_airflow initdb
  check_for_run_hooks || exit $?
  ;;
*)
  log:sep "Starting external command:"
  check_for_db || exit $?
  check_for_run_hooks || exit $?
  "$@"
  ;;
esac

if [ -n "$ZAIRFLOW_ENTRYPOINT_DESTROY_HOOK" ]; then
  log:sep "Starting destroy hook: $ZAIRFLOW_ENTRYPOINT_DESTROY_HOOK"
  "$ZAIRFLOW_ENTRYPOINT_DESTROY_HOOK"
  assert $? "Failed to exec destroy hook" || exit $?
fi
