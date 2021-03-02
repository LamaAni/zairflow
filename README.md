# ZAirflow

### `Beta version`

An opinionated docker image and helm chart for a `simple docker/kubernetes` airflow deploy.

## The repo includes,

1. A [docker image](#Image) for airflow.
1. A [helm chart](#Helm) for airflow.

See examples [here](/examples).

## Supports

1. Python 3.8
1. Airflow 1.10.12
1. Kubernetes/Local executors (celery executor is supported on docker compose only at this time)
1. [KubernetesJobOperator](https://github.com/LamaAni/KubernetesJobOperator) (built in)
1. Database Logger (built in) - airflow logs are saved to the database using SQLAlchemy.
1. dags and plugins synchronization vs a git repo (per branch/tag).
1. linux/arm64 devices. (Tested on linux/arm64/v8 [raspberry pi 4](https://www.raspberrypi.org/products/raspberry-pi-4-model-b/specifications/))

## Resources

The zairflow image is published to [dockerhub](https://hub.docker.com/r/lamaani/zairflow/tags),
and the helm chart is hosted on a github release,

```
lamaani/zairflow:[major].[minor].[patch]
lamaani/zairflow:[major].[minor]
lamaani/zairflow:latest

https://github.com/LamaAni/zairflow/releases/download/[release_tag, eg. 0.5.2]/helm.tar.gz
```

The image is tagged per release. Version definition,

```
[major].[minor].[patch]
```

## Diversions from default airflow config

Changes to the default config:

1. [Core].`logging_config_class` = airflow_db_logger.LOGGING_CONFIG - log to database instead of files.
1. [Kubernetes].`dags_in_image`= True - Expect kubernetes worker dags in the image.
1. [Kubernetes].`kube_client_request_args` = "" - a changed due to a `bug` in the core airflow
   config; the json is not parsed properly.

#### Note

It is recommended to control the airflow configuration using environment variables, like so,

```
export AIRFLOW__[section]__[property]=[value]
```

For more info on setting airflow environment variables see [here](https://airflow.readthedocs.io/en/stable/howto/set-config.html).

## `Envs`

#### Main

| name                         | description                                                                                                                                                                                                                                                                                                                         | type/values                                           | default                          |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | -------------------------------- |
| ZAIRFLOW_RUN_INITDB          | Run `airflow initdb` before the main container process                                                                                                                                                                                                                                                                              | `boolean`                                             | False                            |
| ZAIRFLOW_DB_HOST             | the host for the airflow database, this value is required in order to validate the db                                                                                                                                                                                                                                               | `string`                                              | localhost                        |
| ZAIRFLOW_DB_PORT             | the port for the airflow database                                                                                                                                                                                                                                                                                                   | 1-65535                                               | 5432                             |
| ZAIRFLOW_SKIP_DB_CHECK       | If `true` then skip the db check.                                                                                                                                                                                                                                                                                                   |
|                              |                                                                                                                                                                                                                                                                                                                                     |
| ZAIRFLOW_CONTAINER_TYPE      | The type of the container to execute                                                                                                                                                                                                                                                                                                | scheduler, worker, webserver, flower, initdb, command | None/Empty - will cause an error |
| `...`ZAIRFLOW_CONTAINER_TYPE | Run `airflow [type]`, after preparing the env                                                                                                                                                                                                                                                                                       | scheduler, worker, webserver, flower, initdb          |
| `...`ZAIRFLOW_CONTAINER_TYPE | Run `"$@"`, after preparing the env                                                                                                                                                                                                                                                                                                 | command                                               |
|                              |                                                                                                                                                                                                                                                                                                                                     |
| GIT_AUTOSYNC_REPO_URL        | A uri to the git repo to sync. If exists the git sync process will start. If a git repo already exists on the image at the location of the dags folder, use "internal" (remember to set the correct airflow dag folder path). See [example](/examples/docker-compose/docker-compose-git-autosync.yaml) and notes below on autosync. | `string`                                              | None                             |
| GIT_AUTOSYNC_REPO_BRANCH     | The autosync branch name, if dose not exist uses the default branch. See [example](/examples/docker-compose/docker-compose-git-autosync.yaml) and notes below on autosync.                                                                                                                                                          | `string`                                              | None                             |

#### Advanced

| name                              | description                                                                                                                                                                                                     | type/values | default |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ------- |
| ZAIRFLOW_WAIT_FOR                 | a list of uri, including port (example: localhost:8888) to wait until open on TCP.                                                                                                                              | `string`    | None    |
| ZAIRFLOW_ENTRYPOINT_INIT_HOOK     | A bash script/command to run before the airflow environment (initdb + command) starts                                                                                                                           | `string`    | None    |
| ZAIRFLOW_ENTRYPOINT_RUN_HOOK      | A bash script/command to run before airflow runs (after initdb)                                                                                                                                                 | `string`    | None    |
| ZAIRFLOW_ENTRYPOINT_DESTROY_HOOK  | A bash script/command to run after the airflow environment exists                                                                                                                                               | `string`    | None    |
| ZAIRFLOW_POST_LOAD_USER_CODE      | While calling initdb, INIT HOOK and RUN HOOK, points airflow to load dags and plugins from an empty folder. Allows for initialization without plugin/dag errors and proper initialization of airflow variables. | `boolean`   | False   |
| ZAIRFLOW_AUTO_DETECT_CLUSTER      | Auto detect the cluster config in running in a kubernetes cluster                                                                                                                                               | `boolean`   | true    |
|                                   |                                                                                                                                                                                                                 |
| ZARIFLOW_DB_WAIT_TRIES            | The number of attempts to run when waiting for db tables to be ready                                                                                                                                            | `int`       | 60      |
| ZARIFLOW_DB_WAIT_INTERVAL         | The number of seconds to wait between each db tables test                                                                                                                                                       | `int`       | 1       |
|                                   |                                                                                                                                                                                                                 |
| ZARIFLOW_CONNECTION_WAIT_TRIES    | The number of attempts to run when waiting for a connection                                                                                                                                                     | `int`       | 60      |
| ZARIFLOW_CONNECTION_WAIT_TIMEOUT  | The connection wait timeout                                                                                                                                                                                     | `int`       | 1       |
| ZARIFLOW_CONNECTION_WAIT_INTERVAL | The number of seconds to wait between connection attempts                                                                                                                                                       | `int`       | 1       |
|                                   |                                                                                                                                                                                                                 |
| GIT_AUTOSYNC_REPO_LOCAL_PATH      | Overrides /app directory. The path where the git repo will sync to (remember to set the correct airflow dags/plugins folder path). See notes below on autosync.                                                 | `string`    | None    |

## DB logger

An internal DB logger package was added that writes all logs to a database instead of files. This package can be enabled by setting the `logging_config_class` in the `airflow config`,

```ini
[CORE]
logging_config_class = airflow_db_logger.LOGGING_CONFIG
```

**This package is highly recommended for multi pod implementations**, and was added by default.

Possible package options added to the airflow config,

| section                                 | description                                 | type/values | default                     |
| --------------------------------------- | ------------------------------------------- | ----------- | --------------------------- |
| [db_logger].`SQL_ALCHEMY_CONN`          | The sqlalchemy connection string            | `string`    | [core].`SQL_ALCHEMY_CONN`   |
| [db_logger].`SQL_ALCHEMY_SCHEMA`        | The schema where to put the logging tables. | `string`    | [core].`SQL_ALCHEMY_SCHEMA` |
| [db_logger].`SQL_ALCHEMY_POOL_ENABLED`  | If true enable sql alchemy pool             | `boolean`   | True                        |
| [db_logger].`SQL_ALCHEMY_POOL_SIZE`     | The size of the sqlalchemy pool.            | `int`       | 5                           |
| [db_logger].`SQL_ALCHEMY_MAX_OVERFLOW`  | The max overflow for sqlalchemy             | `int`       | 1                           |
| [db_logger].`SQL_ALCHEMY_POOL_RECYCLE`  | The pool recycle time                       | `int`       | 1800                        |
| [db_logger].`SQL_ALCHEMY_POOL_PRE_PING` | If true, do a ping at the connection start. | `boolean`   | true                        |
| [db_logger].`SQL_ENGINE_ENCODING`       | THe encoding for the sql engine             | `string`    | utf-8                       |

## Git auto-sync

The auto-sync feature runs a backround script, inside the airflow pod, which periodically checks for changes in the git repo and pulls any change
that was detected. See script github reop and details [here](https://github.com/LamaAni/git_autosync).

`The auto sync is recommended for development mode.`

### Configuring the auto sync enviroment

Fist we tell zairflow where the repo is, by setting the `environment variables`:

```yaml
GIT_AUTOSYNC_REPO_URL: [my-repo-uri]
GIT_AUTOSYNC_REPO_BRANCH: [my-repo-branch] # Optional, default = default branch.
```

Then, if in your repo the paths to the airflow dags and plugins are:

```shell
[repo root]/deployment/airflow/dags
[repo root]/deployment/airflow/plugins
```

You need to set the airflow `environment variables` (or in the airflow config file):

```yaml
AIRFLOW__CORE__DAGS_FOLDER: /app/deployment/airflow/dags
AIRFLOW__CORE__PLUGINS_FOLDER: /app/deployment/airflow/plugins
```

##### NOTE: If your image pre-contains dags/plugins, you must copy them into the appropriate paths for dags and plugins

# Helm

A template based deployment chart using helm. To learn more about helm please see [helm](https://helm.sh/) and [helmfile](https://github.com/roboll/helmfile). This [introduction](https://www.digitalocean.com/community/tutorials/an-introduction-to-helm-the-package-manager-for-kubernetes) is also a good read.

## Available executors

In order to simplify the chart, only the following executors are implemented,

1. LocalExecutor
1. KubernetesExecutor
1. SequentialExecutor (Debug)

#### Note: `The celery executor was not implemented due to instabilities in task execution during testing. Currently, it is under consideration, but may not be implemented in future releases.`

#### TL;DR:

See [helmfile example](/examples/docker-compose/dkubernetes-helmfile)

## `Chart values`

#### Note:

The definition `[a].[b]=value` should be translated in the yaml values file as,

```yaml
a:
  b: value
```

#### Main

| name                                        | description                                                                                                            | type/values                                           | default                  |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ------------------------ |
| `nameOverride`                              | Override the name of the chart                                                                                         | `string`                                              | None                     |
| `fullnameOverride`                          | Override the name of the chart and the suffixes                                                                        | `string`                                              | None                     |
| `envs`                                      | global env collection, added to config map                                                                             | `yaml`                                                | None                     |
| `overrideEnvs`                              | global env collection, added to config map, that will override any internal env values that were produced by the chart | `yaml`                                                | None                     |
|                                             |                                                                                                                        |
| `image.pullPolicy`                          | The pull policy                                                                                                        | IfNotPresent, Never, Always                           | IfNotPresent             |
| `image.repository`                          | The image repo                                                                                                         | `string`                                              | lamaani/zairflow         |
| `image.tag`                                 | The image tag                                                                                                          | `string`                                              | latest                   |
|                                             |                                                                                                                        |
| `executor.type`                             | The executor to be used by airflow                                                                                     | SequentialExecutor, LocalExecutor, KubernetesExecutor | LocalExecutor            |
| `executor.workerImagePullPolicy`            | The pull policy                                                                                                        | IfNotPresent, Never, Always                           | `image.pullPolicy`       |
| `executor.workerImageRepository`            | The image repo                                                                                                         | `string`                                              | `image.repository`       |
| `executor.workerImageTag`                   | The image tag                                                                                                          | `string`                                              | `image.tag`              |
|                                             |                                                                                                                        |
| `initdb.enabled`                            | Enabled the initdb job                                                                                                 | `boolean`                                             | true                     |
|                                             |                                                                                                                        |
| `webserver.port`                            | The webserver port to use                                                                                              | `int`                                                 | 8080                     |
| `webserver.terminationGracePeriodSeconds`   | The number of seconds before forced pod termination                                                                    | `int`                                                 | 10                       |
| `webserver.replicas`                        | The number of webserver replicas                                                                                       | `int`                                                 | 1                        |
| `webserver.envs`                            | Environment variables to add to the webserver pods                                                                     | `yaml`                                                | None                     |
| `webserver.resources`                       | Pod resources                                                                                                          | `yaml`                                                | None                     |
|                                             |                                                                                                                        |
| `scheduler.terminationGracePeriodSeconds`   | The number of seconds before forced pod termination                                                                    | `int`                                                 | 10                       |
| `scheduler.replicas`                        | The number of webserver replicas                                                                                       | `int`                                                 | 1                        |
| `scheduler.envs`                            | Environment variables to add to the webserver pods                                                                     | `yaml`                                                | None                     |
| `scheduler.resources`                       | Pod resources                                                                                                          | `yaml`                                                | None                     |
|                                             |                                                                                                                        |
| `postgres.enabled`                          | If true, create a postgres database                                                                                    | `boolean`                                             | true                     |
| `postgres.image`                            | The postgres image, with tag                                                                                           | `string`                                              | postgres:12.2            |
| `postgres.port`                             | The database port to use                                                                                               | `int`                                                 | 5432                     |
| `postgres.terminationGracePeriodSeconds`    | The number of seconds before forced pod termination                                                                    | `int`                                                 | 10                       |
| `postgres.envs`                             | Environment variables to add to the webserver pods                                                                     | `yaml`                                                | None                     |
| `postgres.resources`                        | Pod resources                                                                                                          | `yaml`                                                | None                     |
| `postgres.maxConnections`                   | The maximal number of database connections                                                                             | `int`                                                 | 10000                    |
| `postgres.persist`                          | The maximal number of database connections                                                                             | `bool`                                                | true                     |
| `postgres.pvc`                              | Add a kubernetes PVC to the database, allowing it to persist through db pod restarts                                   | `yaml `                                               | see [here](/helm/values) |
| `postgres.db`                               | The default db                                                                                                         | `string`                                              | airflow                  |
| `postgres.credentials.user`                 | The db username                                                                                                        | `string`                                              | airflow                  |
| `postgres.credentials.password`             | the db password                                                                                                        | `string`                                              | airflow                  |
|                                             |                                                                                                                        |
| `serviceAccount.enabled`                    | If true creates a service account                                                                                      | `boolean`                                             | false                    |
| `serviceAccount.name`                       | The name of the service account to use.                                                                                | `string`                                              | `chart full name`        |
| `serviceAccount.annotations`                | More service account info                                                                                              | `yaml`                                                | None                     |
| `serviceAccount.roleBinding`                | Set a role binding                                                                                                     | `string`                                              | None                     |
| `serviceAccount.roleBindingKind`            | The kind of the role binding                                                                                           | `string`                                              | `Role`                   |
| `serviceAccount.allowKubernetesAccess`      | If true generates the kubernetes access role binding                                                                   | `boolean`                                             | true                     |
| `serviceAccount.allowKubernetesAccessRules` | The rules for the zairflow worker kubernetes access                                                                    | `yaml`                                                |                          |

#### Advanced

Yaml injection, use with care,

| name                            | description | type/values | applies to types                       |
| ------------------------------- | ----------- | ----------- | -------------------------------------- |
| `[type].injectContainerYaml`    | yaml inject | `yaml`      | webserver, scheduler, postgres, initdb |
| `[type].injectTemplateSpecYaml` | yaml inject | `yaml`      | webserver, scheduler, postgres, initdb |
| `[type].injectSpecYaml`         | yaml inject | `yaml`      | webserver, scheduler, postgres, initdb |
| `[type].injectYamlMetadata`     | yaml inject | `yaml`      | serviceAccount                         |
| `[type].injectYaml`             | yaml inject | `yaml`      | serviceAccount                         |

## Creating a derived docker image

If you are creating a derived image, and you are installing airflow using pip,
or in some way overriding `/usr/local/bin/airflow` or the `airflow` cli with a
new airflow install. For a KubernetesExecutor deployment you must override the
cli airflow command as `root` with,

```shell
ln -sf /scripts/image/invoke_airflow /usr/local/bin/airflow
```

# Licence

Copyright ©
`Zav Shotan` and other [contributors](../../graphs/contributors).
It is free software, released under the MIT licence, and may be redistributed under the terms specified in [LICENSE](LICENSE).
