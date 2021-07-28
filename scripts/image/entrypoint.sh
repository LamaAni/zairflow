#!/usr/bin/env bash
: ${SCRIPTS_PATH:="$(dirname $(dirname $(realpath "$BASH_SOURCE[0]")))"}
# shellcheck disable=SC1091
source "$SCRIPTS_PATH/common.sh"

: "${ZAIRFLOW_RUN_INIT_ENVIRONMENT:="false"}"
: "${ZAIRFLOW_CONTAINER_TYPE:="standalone"}"

if [ -n "$ZAIRFLOW_ENTRYPOINT_INIT_HOOK" ]; then
  log:sep "Starting init hook: $ZAIRFLOW_ENTRYPOINT_INIT_HOOK"
  "$ZAIRFLOW_ENTRYPOINT_INIT_HOOK"
  assert $? "Failed to exec init hook" || exit $?
fi

# shellcheck disable=SC1091
source "$SCRIPTS_PATH/image/init_zairflow_env.sh" || exit $?

# post loading of dags and plugins.
ZAIRFLOW_POST_LOAD_USER_CODE_REVERT_AIRFLOW_DAGS_FOLDER=""
ZAIRFLOW_POST_LOAD_USER_CODE_REVERT_AIRFLOW_PLUGINS_FOLDER=""

function prepare_post_load_user_code() {
  if [ "$ZAIRFLOW_POST_LOAD_USER_CODE" == "true" ]; then
    log:sep "Initializing airflow without user code (dags and plugins)"
    export ZAIRFLOW_POST_LOAD_USER_CODE_REVERT_AIRFLOW_DAGS_FOLDER="$AIRFLOW__CORE__DAGS_FOLDER"
    export ZAIRFLOW_POST_LOAD_USER_CODE_REVERT_AIRFLOW_PLUGINS_FOLDER="$AIRFLOW__CORE__PLUGINS_FOLDER"
    mkdir -p /tmp/not_a_dags_folder &&
      mkdir -p /tmp/not_a_plugins_folder
    assert $? "Failed to create post_load temp folders"
    export AIRFLOW__CORE__DAGS_FOLDER="/tmp/not_a_dags_folder"
    export AIRFLOW__CORE__PLUGINS_FOLDER="/tmp/not_a_plugins_folder"
  fi
}

function attach_post_load_user_code() {
  if [ "$ZAIRFLOW_POST_LOAD_USER_CODE" == "true" ]; then
    log:sep "Adding back user code after initialization"
    export AIRFLOW__CORE__DAGS_FOLDER="$ZAIRFLOW_POST_LOAD_USER_CODE_REVERT_AIRFLOW_DAGS_FOLDER"
    export AIRFLOW__CORE__PLUGINS_FOLDER="$ZAIRFLOW_POST_LOAD_USER_CODE_REVERT_AIRFLOW_PLUGINS_FOLDER"
  fi
}

function invoke_run_hooks() {
  if [ -n "$ZAIRFLOW_ENTRYPOINT_RUN_HOOK" ]; then
    log:sep "Starting run hook: $ZAIRFLOW_ENTRYPOINT_RUN_HOOK"
    "$ZAIRFLOW_ENTRYPOINT_RUN_HOOK"
    assert $? "Failed to exec run hook" || exit $?
  fi
}

function check_default_invokes() {
  if [ "$ZAIRFLOW_RUN_INIT_ENVIRONMENT" == "true" ]; then
    airflow_init_environment
  fi
}

# for the case where user code is loaded after the init.
prepare_post_load_user_code || exit $?
case "$ZAIRFLOW_CONTAINER_TYPE" in
worker)
  # a worker
  check_default_invokes || exit $?
  invoke_run_hooks || exit $?
  attach_post_load_user_code || exit $?
  log:sep "Starting worker"
  invoke_airflow worker
  ;;
scheduler)
  check_default_invokes || exit $?
  invoke_run_hooks || exit $?
  attach_post_load_user_code || exit $?
  log:sep "Starting scheduler"
  invoke_airflow scheduler
  ;;
webserver)
  check_default_invokes || exit $?
  invoke_run_hooks || exit $?
  attach_post_load_user_code || exit $?
  
  log:sep "Starting webserver"
  invoke_airflow webserver
  ;;
flower)
  invoke_run_hooks || exit $?
  attach_post_load_user_code || exit $?
  log:sep "Starting flower"
  invoke_airflow flower
  ;;
init_environment)
  invoke_run_hooks || exit $?
  airflow_init_environment || exit $?
  ;;
standalone)
  log:info "${cyan}Running as standalone airflow container${end_color}"
  export AIRFLOW__CORE__EXECUTOR="$AIRFLOW_STANDALONE_EXECUTOR"
  invoke_run_hooks || exit $?
  airflow_init_environment || exit $?
  invoke_airflow scheduler &
  export AIRFLOW_SCHEDULER_PID=$!
  invoke_airflow webserver
  kill $AIRFLOW_SCHEDULER_PID
  ;;
command)
  check_default_invokes || exit $?
  invoke_run_hooks || exit $?
  log:sep "Starting external command:"
  attach_post_load_user_code || exit $?
  "$@"
  ;;
*)
  assert 3 "Container type not recognized: $ZAIRFLOW_CONTAINER_TYPE" || exit $?
  ;;
esac

if [ -n "$ZAIRFLOW_ENTRYPOINT_DESTROY_HOOK" ]; then
  log:sep "Starting destroy hook: $ZAIRFLOW_ENTRYPOINT_DESTROY_HOOK"
  "$ZAIRFLOW_ENTRYPOINT_DESTROY_HOOK"
  assert $? "Failed to exec destroy hook" || exit $?
fi
