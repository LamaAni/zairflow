#!/bin/bash
: "${SCRIPTS_PATH:="$(dirname "$(dirname "$(realpath "${BASH_SOURCE[0]}")")")"}"
: "${ZAIRFLOW_AIRFLOW_COMMAND_PATH="/usr/local/bin/airflow"}"

function invoke_airflow() {
  # kill everything if failed.
  "${ZAIRFLOW_AIRFLOW_COMMAND_PATH}" "$@"
  assert $? "Failed: airflow $@" || exit $?
}

function airflow_get_config_vals() {
  python3 "$SCRIPTS_PATH/python/airflow_get_config_vals.py" "$@"
}

function airflow_check_db() {
  log:info "Checking airflow database"
  python3 "$SCRIPTS_PATH/python/airflow_check_db.py"
  assert $? "Airflow database check failed" || return $?
  log:info "Airflow database OK!"
}

function airflow_init_core_files() {
  if [ -n "$ZAIRFLOW_WEBSERVER_CONFIG_PATH" ]; then

    [ -f "$ZAIRFLOW_WEBSERVER_CONFIG_PATH" ]
    assert $? "Webserver config path not found @ $ZAIRFLOW_WEBSERVER_CONFIG_PATH" || return $?

    ZAIRFLOW_WEBSERVER_CONFIG_PATH="$(realpath "$ZAIRFLOW_WEBSERVER_CONFIG_PATH")"
    assert $? "Faild to resove webserver config path $ZAIRFLOW_WEBSERVER_CONFIG_PATH" || return $?

    ln -sf "$ZAIRFLOW_WEBSERVER_CONFIG_PATH" "$AIRFLOW_HOME/webserver_config.py"
    assert $? "Faild to link webserver config path $ZAIRFLOW_WEBSERVER_CONFIG_PATH -> $AIRFLOW_HOME/webserver_config.py" || return $?
    log:info "Webserver config linked: $ZAIRFLOW_WEBSERVER_CONFIG_PATH -> $AIRFLOW_HOME/webserver_config.py "

  else
    warn $? "Webserver config path not defined, skipped"
  fi

  local zairflow_worker_pod_yaml="/airflow/zairflow_worker_pod.yaml"

  echo "$ZAIRFLOW_KUBERNETES_EXECUTOR_WORKER_CONFIG" | base64 -d >|"$zairflow_worker_pod_yaml"
  assert $? "Failed to create kuberntes executor worker default configuration @ $zairflow_worker_pod_yaml" || return $?
  log:info "Kuberntes worker configuration created @ $zairflow_worker_pod_yaml"
}

function airflow_init_environment() {
  log:sep "Initializing airflow database"
  invoke_airflow db init
  assert $? "Failed to perform init db" || return $?

  log:sep "Initializing airflow environment"
  python3 "$SCRIPTS_PATH/python/airflow_initialize_environment.py"
  assert $? "Failed to perform environment initialization" || return $?
}

function airflow_load_kubernetes_configuration() {
  export IS_KUBERNETES=1
  kubectl cluster-info 2>&1 >/dev/null
  assert_warning $? "Could not retrieve cluster info. Continue assuming not running in kuberntes." || IS_KUBERNETES=0

  if [ $IS_KUBERNETES -eq 1 ]; then
    if [ "$ZAIRFLOW_AUTO_DETECT_CLUSTER" == "true" ] && [ -n "$KUBERNETES_SERVICE_HOST" ]; then
      log:info "Autodetected airflow kubernetes in cluster"
      ": ${AIRFLOW__KUBERNETES__IN_CLUSTER:="True"}"

      AIRFLOW__KUBERNETES__NAMESPACE=$(airflow_get_config_vals kubernetes.namespace)
      assert_warning $? "Failed to load kuberntes namespace from config, trying to use current" || AIRFLOW__KUBERNETES__NAMESPACE=""

      if [ -z "$AIRFLOW__KUBERNETES__NAMESPACE" ]; then
        if [ -f '/var/run/secrets/kubernetes.io/serviceaccount/namespace' ]; then
          AIRFLOW__KUBERNETES__NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
          log:info "Autodetected current namesace @ $AIRFLOW__KUBERNETES__NAMESPACE"
        else
          assert 5 "Failed to find a kubernetes namespace to run in. " || exit $?
        fi
      fi
      log:info "Running executor worker pods in namespace $AIRFLOW__KUBERNETES__NAMESPACE"
    fi
  fi

  if [ -n "$AIRFLOW__KUBERNETES__IN_CLUSTER" ]; then
    export AIRFLOW__KUBERNETES__IN_CLUSTER
  fi
  if [ -n "$AIRFLOW__KUBERNETES__NAMESPACE" ]; then
    export AIRFLOW__KUBERNETES__NAMESPACE
  fi
  if [ -n "$AIRFLOW__KUBERNETES__WORKER_CONTAINER_REPOSITORY" ]; then
    export AIRFLOW__KUBERNETES__WORKER_CONTAINER_REPOSITORY
  fi
}
