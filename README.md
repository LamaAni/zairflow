# ZAirflow

### `Alpha version`

An opinionated docker image and helm chart for a simple Kubernetes airflow deploy.

The repo includes,

1. A docker image for airflow.
1. A helm chart for airflow.

See examples [here](/examples).

# `zairflow` Image

The zairflow image is built and published to dockerhub @,
```
lamaani/zairflow:[major].[minor].[patch]
lamaani/zairflow:[major].[minor]
lamaani/zairflow:latest
```
The image is tagged per release. Version definition is `[major].[minor].[patch]`, where 
for each build the patch number is updated. The minor version will be updated for every stable release.

## Envs

#### Main

name | description | type/values | default
---|---|---|---
ZAIRFLOW_RUN_INITDB | Run `airflow initdb` before the main container process | `boolean` | False
ZAIRFLOW_DB_HOST | the host for the airflow database, this value is required in order to validate the db | `string` | localhost
ZAIRFLOW_DB_PORT | the port for the airflow database | 1-65535 | 5432
|||
ZAIRFLOW_CONTAINER_TYPE | The type of the container to execute | scheduler/worker/webserver/flower/initdb/command | None/Empty - will cause an error
`...`ZAIRFLOW_CONTAINER_TYPE | Run `airflow [type]`, after preparing the env | scheduler/worker/webserver/flower/initdb 
`...`ZAIRFLOW_CONTAINER_TYPE | Run `"$@"`, after preparing the env | command
|||
ZAIRFLOW_GIT_AUTOSYNC_URI| A uri to the git repo to sync. If exists the git sync process will start. If a git repo already exists on the image at the location of the dags folder, use "internal" (remember to set the correct airflow dag folder path). See [example](/examples/docker-compose/docker-compose-git-autosync.yaml). | `string` | None
ZAIRFLOW_GIT_AUTOSYNC_PATH| The path where the git repo will sync to (remember to set the correct airflow dags/plugins folder path). See [example](/examples/docker-compose/docker-compose-git-autosync.yaml). | `string` | None

#### Advanced

name | description | type/values | default
---|---|---|---
ZAIRFLOW_WAIT_FOR | a list of uri, including port (example: localhost:8888) to wait until open on TCP. | `string` | None
ZAIRFLOW_ENTRYPOINT_INIT_HOOK | A bash script/command to run before the airflow environment (initdb + command) starts | `string` | None
ZAIRFLOW_ENTRYPOINT_RUN_HOOK | A bash script/command to run before airflow runs (after initdb) | `string` | None
ZAIRFLOW_ENTRYPOINT_DESTROY_HOOK | A bash script/command to run after the airflow environment exists | `string` | None
ZAIRFLOW_POST_LOAD_USER_CODE | While calling initdb, INIT HOOK and RUN HOOK, points airflow to load dags and plugins from an empty folder. Allows for initialization without plugin/dag errors and proper initialization of airflow variables. | `boolean` | False


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
