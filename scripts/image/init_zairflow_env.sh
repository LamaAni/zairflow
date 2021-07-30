#!/usr/bin/env bash
: "${SCRIPTS_PATH:="$(dirname "$(dirname "$(realpath "${BASH_SOURCE[0]}")")")"}"
: "${ZAIRFLOW_ENV_INITIALIZED_TS_PATH:="/airflow/zairflow_initialized.ts"}"

source "$SCRIPTS_PATH/common.sh"

function load_airflow_environment_variables() {
  # zairflow execution
  : "${ZAIRFLOW_CONTAINER_TYPE:="worker"}"
  : "${ZAIRFLOW_WAIT_FOR:=""}"
  : "${ZAIRFLOW_AUTO_DETECT_CLUSTER:="true"}"
  : "${ZAIRFLOW_POST_LOAD_USER_CODE:="false"}"

  # Default postgres
  : "${ZAIRFLOW_DB_HOST:="localhost"}"
  : "${ZAIRFLOW_SKIP_DB_CHECK:="false"}"
  : "${ZAIRFLOW_DB_PORT:="5432"}"

  # default connections.
  : "${AIRFLOW__CORE__DAGS_FOLDER:="/app"}"
  : "${AIRFLOW__WEBSERVER__BASE_URL:="localhost:8080"}"
  : "${AIRFLOW__CLI__ENDPOINT_URL:="localhost:8080"}"

  airflow_load_kubernetes_configuration
  assert $? "Failed to load kubernetes configuration"
}

function prepare_airflow_env() {
  # shellcheck disable=SC1091
  log:info "Preparing zairflow environment as user '$(whoami)'"

  ###########################
  # Configuration
  if [ -n "$GIT_AUTOSYNC_REPO_URL" ]; then
    log:sep "Checking git autosync"
    "$SCRIPTS_PATH/image/init_git_autosync.sh"
    assert $? "Failed to initialize git auto-sync" || return $?
  fi

  if [ "$ZAIRFLOW_SKIP_DB_CHECK" != "true" ]; then
    log:sep "Checking database"
    airflow_check_db
    assert $? "Airflow database not ready" || return $?
  fi

  wait_for_resource_connections
  assert $? "Failed waiting for resource connections" || return $?

  log:sep "Finalizing"
  airflow_init_core_files || return $?

  # Mark timestamp
  date >"$ZAIRFLOW_ENV_INITIALIZED_TS_PATH"
  assert $? "Failed to mark airflow env initialized." || return $?

  export AIRFLOW_ENV_PREPARED="true"
  export AIRFLOW__CORE__DAGS_FOLDER
  log:info "Airflow env ready, dags @ $AIRFLOW__CORE__DAGS_FOLDER"
}

function is_airflow_env_loaded() {
  if [ "$AIRFLOW_ENV_PREPARED" == "true" ] || [ -f "$ZAIRFLOW_ENV_INITIALIZED_TS_PATH" ]; then
    return 0
  fi
  return 1
}

load_airflow_environment_variables
assert $? "Failed to load airflow environment variables" || exit $?

is_airflow_env_loaded || prepare_airflow_env
assert $? "Error while preparing airflow environment. exiting." || exit $?
