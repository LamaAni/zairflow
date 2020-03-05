# ZAirflow

An opinionated docker image and helm chart for a simple Kubernetes airflow deploy.

The repo includes,

1. A docker image for airflow.
1. A helm chart for airflow.

### `Alpha version`

# `zairflow` Image

The zairflow image is built and published to dockerhub at,
`lamaani/zairflow`, and is tagged to each release.

## Envs

1. ZAIRFLOW_DB_HOST - the host for the airflow database (default to localhost)
1. ZAIRFLOW_DB_PORT - the port for the airflow database (default to pg, 5432)
1. ZAIRFLOW_CONTAINER_TYPE - array, space separated of the pod types. applies only to the entrypoint script. Can be
   1. scheduler
   1. worker
   1. webserver
   1. flower
   1. initdb
1. ZAIRFLOW_RUN_INITDB - Run the init db in the entrypoint.
1. ZAIRFLOW_WAIT_FOR - a list of uri, including port (example: localhost:8888) to wait until open on TCP.
1. ZAIRFLOW_GIT_AUTOSYNC_URI - a uri to the git repo to sync. If a git repo already exists on the image at the location of the dags folder, use "internal" (remember to set the correct airflow dag folder path).
1. ZAIRFLOW_GIT_AUTOSYNC_PATH - The path where the git repo will sync to (remember to set the correct airflow dag folder path).
1. ZAIRFLOW_ENTRYPOINT_INIT_HOOK - A hook that runs before the airflow environment starts (including built in initdb, ZAIRFLOW_RUN_INITDB)
1. ZAIRFLOW_ENTRYPOINT_RUN_HOOK - A hook that runs after the airflow environment starts (including built in initdb, ZAIRFLOW_RUN_INITDB)
1. ZAIRFLOW_ENTRYPOINT_DESTROY_HOOK - A hook that runs after the airflow environment exists (mostly applies to initdb)
1. ZAIRFLOW_POST_LOAD_USER_CODE - If true, user code in `dags` and `plugins` will be loaded only when
   service is started, and will be ignored while initializing (initdb or init hooks).

# Helm

if using kubernetes executor dags in image is true.

## Available executors

1. LocalExecutor
1. KubernetesExecutor
1. SequentialExecutor (Debug)

The celery executor was has not been implemented. Currently, it is under consideration,
and may not be implemented in future releases.

Note: ZAirflow overrides the default dags folder. You must set `AIRFLOW__CORE__DAGS_FOLDER` env
in order to change the dags folder. airflow.cfg will be ignored.
