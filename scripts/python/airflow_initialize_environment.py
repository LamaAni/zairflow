import yaml
import os
import json
from typing import List
from airflow.api.common.experimental.pool import get_pool, create_pool
from sqlalchemy.orm import Session
from airflow.models import Connection, Pool, Variable
from airflow.utils.db import provide_session
from common import log

def get_yaml_from_file_or_none(fpath: str):
    assert fpath is None or isinstance(fpath, str)
    if fpath is None or not os.path.exists(fpath):
        return None
    as_yaml = ""
    with open(fpath, "r") as raw:
        as_yaml = raw.read()
    as_yaml = as_yaml.format(**os.environ)

    log.info("Loaded yaml defaults from: " + fpath)
    return as_yaml


log.info("Initializing airflow configuration")

# checking airflow env locations
yamls: List[str] = [
    os.environ.get("ZAIRFLOW_INIT_ENV_YAML", None),
    get_yaml_from_file_or_none(os.environ.get("ZAIRFLOW_INIT_ENV_YAML_FILEPATH")),
]

yamls = [v for v in yamls if v is not None]
if len(yamls) > 0:

    def load_variables(config: dict):
        variables: dict = config.get("variables", None)
        if variables is None or not isinstance(variables, dict):
            log.info("No variables found, skipping")
            return

        log.info("Loading variabels from config...")
        for key in variables.keys():
            val = variables.get(key)
            if val is None:
                continue

            if Variable.get(key=key, default_var=None) is not None:
                log.info(f"Variable exists, skipping: {key}")
                continue
            log.info("Setting variable: " + key)
            Variable.set(
                key=key,
                value=val,
                serialize_json=val is not None and not isinstance(val, (int, str)),
            )

    @provide_session
    def load_pools(
        config: dict,
        session: Session = None,
    ):
        pools: dict = config.get("pools", None)
        if pools is None:
            log.info("No pools found, skipping")
            return

        log.info("Loading pools from config...")
        for key in pools.keys():
            val = pools.get(key)

            pool = session.query(Pool).filter_by(pool=key).first()
            if pool is not None:
                log.info(f"Pool exists, skipping: {key}")
                continue

            log.info("Setting pool: " + key)
            pool = Pool(pool=key)
            if isinstance(val, dict):
                pool.description = val.get("description", "Loaded by zairflow")
                pool.slots = val.get("slots", -1)
            else:
                assert isinstance(val, (int, float))
                pool.description = "Loaded from zairflow init"
                pool.slots = val or -1
            session.add(pool)
        session.commit()

    @provide_session
    def load_connections(
        config: dict,
        session: Session = None,
    ):
        connections = config.get("connections", None)
        if connections is None:
            log.info("No connections found, skipping")
            return

        log.info("Loading variabels from config...")
        for key in connections.keys():
            val: dict = connections.get(key)
            if not isinstance(val, dict):
                log.warn(f"Connection {key} skipped. Value must be a dictionary.")

            connection = session.query(Connection).filter_by(conn_id=key).first()
            if connection is not None:
                log.info(f"Connection exists, skipping: {key}")
                continue

            log.info("Setting connection: " + key)
            extra = val.get("extra", None)
            if extra is not None and not isinstance(extra, (int, str)):
                extra = json.dumps(extra)

            connection = Connection(
                conn_id=key,
                conn_type=val.get("conn_type", None),
                host=val.get("host", None),
                login=val.get("login", None),
                password=val.get("password", None),
                schema=val.get("schema", None),
                port=val.get("port", None),
                extra=extra,
            )
            session.add(connection)
        session.commit()

    config = {}
    for y in yamls:
        config.update(yaml.safe_load(y.format(**os.environ)) or {})

    load_variables(config=config)
    load_connections(config=config)
    load_pools(config=config)
else:
    log.info("No yaml configurations found")