#!/usr/bin/env bash

function prepare_airflow_env() {
  CUR_PATH="$SCRIPTS_PATH"
  : ${CUR_PATH:="$(realpath $(dirname $(realpath "$BASH_SOURCE[0]")))"}
  source "$CUR_PATH/common.sh"

  log:sep "Prepare zairflow environment as user '$(whoami)'"

  ###########################
  # Configuration

  # zairflow execution
  : ${ZAIRFLOW_CONTAINER_TYPE:="worker"}
  : ${ZAIRFLOW_WAIT_FOR:=""}
  : ${ZAIRFLOW_DAGS_FOLDER:="/app"}
  : ${ZAIRFLOW_AUTO_DETECT_CLUSTER:="true"}
  : ${ZAIRFLOW_POST_LOAD_USER_CODE:="false"}

  ZAIRFLOW_WAIT_FOR=($ZAIRFLOW_WAIT_FOR)

  if [ -z "$MAIN_HOST" ]; then
    # This is the main container.
    MAIN_HOST="localhost"
  fi

  # Default postgres
  : "${DB_HOST:="$MAIN_HOST"}"
  : "${DB_PORT:="5432"}"

  # default connections.
  : ${AIRFLOW__CLI__ENDPOINT_URL:="$MAIN_HOST:8080"}
  : ${AIRFLOW__WEBSERVER__BASE_URL:="$MAIN_HOST:8080"}
  : ${AIRFLOW__CORE__DAGS_FOLDER:="/app"}

  # kubernetes
  export IS_KUBERNETES=1
  kubectl cluster-info
  assert_warning $? "Could not retrieve cluster info. Continue assuming not running in kuberntes." || IS_KUBERNETES=0

  if [ $IS_KUBERNETES -eq 1 ]; then
    if [ "$ZAIRFLOW_AUTO_DETECT_CLUSTER" == "true" ] && [ -n "$KUBERNETES_SERVICE_HOST" ]; then
      log:info "Autodetected airflow kubernetes in cluster"
      : ${AIRFLOW__KUBERNETES__IN_CLUSTER:="True"}
      export AIRFLOW__KUBERNETES__IN_CLUSTER

      AIRFLOW__KUBERNETES__NAMESPACE=$(get_airflow_config_vals kubernetes.namespace)
      assert $? "Failed to load kuberntes namespace from config: $AIRFLOW__KUBERNETES__NAMESPACE" || exit $?

      if [ -z "$AIRFLOW__KUBERNETES__NAMESPACE" ] && [ -f '/var/run/secrets/kubernetes.io/serviceaccount/namespace' ]; then
        AIRFLOW__KUBERNETES__NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
        log:info "Autodetected current namesace @ $AIRFLOW__KUBERNETES__NAMESPACE"
        export AIRFLOW__KUBERNETES__NAMESPACE
      fi
      log:info "Running executor worker pods in namespace $AIRFLOW__KUBERNETES__NAMESPACE"
    fi
    export AIRFLOW__KUBERNETES__WORKER_CONTAINER_REPOSITORY
  fi

  log:sep "Checking dependencies..."
  # postgres validate
  log:info "Waiting for the database to be ready @ $DB_HOST:$DB_PORT..."
  wait_for_connection "$DB_HOST:$DB_PORT" || return $?
  assert $? "Failed to find database. Exiting." || return $?

  for wait_for_url in "${ZAIRFLOW_WAIT_FOR[@]}"; do
    log:info "Waiting for $wait_for_url to be ready..."
    wait_for_connection "$wait_for_url" || return $?
    assert $? "Failed connecting to $wait_for_url"
  done

  if [ -n "$ZAIRFLOW_GIT_AUTOSYNC_URI" ]; then
    local sync_folder="$AIRFLOW__CORE__DAGS_FOLDER"
    if [ -n "$ZAIRFLOW_DAGS_SUBFOLDER" ]; then
      AIRFLOW__CORE__DAGS_FOLDER="$AIRFLOW__CORE__DAGS_FOLDER/$ZAIRFLOW_DAGS_SUBFOLDER"
    fi
    export AIRFLOW__CORE__DAGS_FOLDER

    log:sep "Starting git auto-sync to $ZAIRFLOW_GIT_AUTOSYNC_URI"
    "$CUR_PATH/init_git_autosync.sh" "$ZAIRFLOW_GIT_AUTOSYNC_URI" "$sync_folder" "$ZAIRFLOW_DAGS_SUBFOLDER"
    assert $? "Failed to initialize git autosync" || return $?
  fi
}

if [ "$AIRFLOW_ENV_PREPARED" != "true" ]; then
  export AIRFLOW_ENV_PREPARED="true"
  prepare_airflow_env
  assert $? "Error while preparing airflow environment. exiting." || exit $?
  export AIRFLOW__CORE__DAGS_FOLDER
  log:info "Airflow env ready, dags @ $AIRFLOW__CORE__DAGS_FOLDER"
else
  log:info "Airflow env has already been prepared."
fi
