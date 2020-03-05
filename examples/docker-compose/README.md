# Examples for using docker compose

## Build a docker image with the dags/plugins and run.

#### File: `docker-compose.yaml`
#### Commands:
```shell
docker-compose build
docker-compose up
```

## Use a git autosync to load the dags/plugins into airflow

#### File: `docker-compose-git-autosync.yaml`
#### Commands:
```shell
docker compose -f ./docker-compose-git-autosync.yaml up
```