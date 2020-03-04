# airflow_db_logger

An internal implementation to allow logging directly to a database
using SqlAlchemy

## Configuration

Uses the airflow config, under the section `db_logger`. You can add a section to the airflow
configuration of apply these values using envs, like so,
```shell
export AIRFLOW__DB_LOGGER_[config value name]="my_value"
```

### Possible values

name | info | default
---|---|---
SQL_ALCHEMY_SCHEMA | The schema where to put the logging tables. | Use airflow core schema
SQL_ALCHEMY_POOL_ENABLED | If true enable sql alchemy pool | True
SQL_ALCHEMY_POOL_SIZE | The size of the sqlalchemy pool. | 5
SQL_ALCHEMY_MAX_OVERFLOW | The max overflow for sqlalchemy | 1
SQL_ALCHEMY_POOL_RECYCLE | The pool recycle time | 1800
SQL_ALCHEMY_POOL_PRE_PING | If true, do a ping at the connection start. | true
SQL_ENGINE_ENCODING | THe encoding for the sql engine | utf-8

