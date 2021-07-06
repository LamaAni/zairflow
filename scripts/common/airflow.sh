#!/bin/bash
function get_airflow_config_vals() {
  python3 "$SCRIPTS_PATH/image/get_airflow_config_vals.py" "$@"
}
