#!/bin/bash
function airflow_get_config_vals() {
  python3 "$SCRIPTS_PATH/common/airflow_get_config_vals.py" "$@"
}

function airflow_check_db() {
}

function check_airflow_db() {
  if [ "$ZAIRFLOW_RUN_INITDB" == "true" ]; then
    invoke_init_db || return $?
  else
    log:sep "Waiting for airflow db initialization"
    python3 "$SCRIPTS_PATH/image/check_airflow_db.py"
    assert $? "Airflow database was not initialized" || return $?
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
