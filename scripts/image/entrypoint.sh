#!/usr/bin/env bash
: ${SCRIPTS_PATH:="$(dirname $(dirname $(realpath "$BASH_SOURCE[0]")))"}
# shellcheck disable=SC1091
source "$SCRIPTS_PATH/common.sh"

: ${ZAIRFLOW_RUN_INITDB:="false"}
: ${ZAIRFLOW_CONTAINER_TYPE:="standalone"}

if [ "$ZAIRFLOW_CONTAINER_TYPE" == "standalone" ]; then
  export ZAIRFLOW_SKIP_DB_CHECK="true"
  export ZAIRFLOW_WAIT_FOR=""
fi

if [ -n "$ZAIRFLOW_ENTRYPOINT_INIT_HOOK" ]; then
  log:sep "Starting init hook: $ZAIRFLOW_ENTRYPOINT_INIT_HOOK"
  "$ZAIRFLOW_ENTRYPOINT_INIT_HOOK"
  assert $? "Failed to exec init hook" || exit $?
fi

# shellcheck disable=SC1091
source "$SCRIPTS_PATH/image/prepare_airflow_env.sh" || exit $?

function invoke_airflow() {
  # kill everything if failed.
  airflow "$@"
  assert $? "Failed: airflow $@" || exit $?
}

function attach_webserver_config_file() {
  [ -n "$ZAIRFLOW_WEBSERVER_CONFIG_PATH" ]
  warn $? "Webserver config path not defined, skipped" || return 0

  [ -f "$ZAIRFLOW_WEBSERVER_CONFIG_PATH" ]
  assert $? "Webserver config path not found @ $ZAIRFLOW_WEBSERVER_CONFIG_PATH" || return $?

  ZAIRFLOW_WEBSERVER_CONFIG_PATH="$(realpath "$ZAIRFLOW_WEBSERVER_CONFIG_PATH")"
  assert $? "Faild to resove webserver config path $ZAIRFLOW_WEBSERVER_CONFIG_PATH" || return $?

  ln -sf "$ZAIRFLOW_WEBSERVER_CONFIG_PATH" "$AIRFLOW_HOME/webserver_config.py"
  assert $? "Faild to link webserver config path $ZAIRFLOW_WEBSERVER_CONFIG_PATH -> $AIRFLOW_HOME/webserver_config.py"
  log:info "Webserver config linked: $ZAIRFLOW_WEBSERVER_CONFIG_PATH -> $AIRFLOW_HOME/webserver_config.py "
}

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

function invoke_init_db() {
  log:sep "Initializing airflow db.."
  invoke_airflow db init
  assert $? "Failed to perform init db" || return $?
  log:sep "Initializing airflow environment"
  python3 /scripts/image/init_airflow_env.py
  assert $? "Failed to initialize environment" || return $?
}

function check_for_db() {
  if [ "$ZAIRFLOW_RUN_INITDB" == "true" ]; then
    invoke_init_db || return $?
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

# for the case where user code is loaded after the init.
prepare_post_load_user_code || exit $?
case "$ZAIRFLOW_CONTAINER_TYPE" in
worker)
  # a worker
  check_for_db || exit $?
  check_for_run_hooks || exit $?
  attach_post_load_user_code || exit $?
  log:sep "Starting worker"
  invoke_airflow worker
  ;;
scheduler)
  check_for_db || exit $?
  check_for_run_hooks || exit $?
  attach_post_load_user_code || exit $?
  log:sep "Starting scheduler"
  invoke_airflow scheduler
  ;;
webserver)
  check_for_db || exit $?
  check_for_run_hooks || exit $?
  attach_post_load_user_code || exit $?
  attach_webserver_config_file || exit $?
  log:sep "Starting webserver"
  invoke_airflow webserver
  ;;
flower)
  check_for_run_hooks || exit $?
  attach_post_load_user_code || exit $?
  log:sep "Starting flower"
  invoke_airflow flower
  ;;
initdb)
  check_for_run_hooks || exit $?
  invoke_init_db
  ;;
standalone)
  log:info "${cyan}Running as standalone airflow container${end_color}"
  export AIRFLOW__CORE__EXECUTOR="$AIRFLOW_STANDALONE_EXECUTOR"
  attach_webserver_config_file || exit $?
  check_for_run_hooks || exit $?
  invoke_init_db || exit $?
  invoke_airflow scheduler &
  export AIRFLOW_SCHEDULER_PID=$!
  invoke_airflow webserver
  kill $AIRFLOW_SCHEDULER_PID
  ;;
command)
  check_for_db || exit $?
  check_for_run_hooks || exit $?
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
