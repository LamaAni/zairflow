import yaml
import os
import logging
import json
from typing import List


def get_yaml_from_file_or_none(fpath: str):
    assert fpath is None or isinstance(fpath, str)
    if fpath is None or not os.path.exists(fpath):
        return None
    as_yaml = ""
    with open(fpath, "r") as raw:
        as_yaml = raw.read()
    return as_yaml


# checking airflow env locations
yamls: List[str] = [
    os.environ.get("ZAIRFLOW_INIT_ENV_YAML", None),
    get_yaml_from_file_or_none(os.environ.get("ZAIRFLOW_INIT_ENV_YAML_FILEPATH")),
]

yamls = [v for v in yamls if v is not None]
if len(yamls) > 0:
    from airflow.api.common.experimental.pool import get_pool, create_pool
    from sqlalchemy.orm import Session
    from airflow.models import Connection, Pool, Variable
    from airflow.utils.db import provide_session
    from airflow.configuration import conf

    def load_variables(config: dict):
        variables: dict = config.get("variables", None)
        if variables is None or not isinstance(variables, dict):
            return

        logging.info("Loading variabels from config...")
        for key in variables.keys():
            val = variables.get(key)
            if val is None:
                continue

            if Variable.get(key=key, default_var=None) is not None:
                logging.info(f"Variable exists, skipping: {key}")
                continue
            logging.info("Setting variable: " + key)
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
        pools:dict = config.get("pools", None)
        if pools is None:
            return

        logging.info("Loading variabels from config...")
        for key in pools.keys():
            val = pools.get(key)

            pool = session.query(Pool).filter_by(pool=key).first()
            if pool is not None:
                logging.info(f"Pool exists, skipping: {key}")
                continue

            logging.info("Setting pool: " + key)
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
            return

        logging.info("Loading variabels from config...")
        for key in connections.keys():
            val: dict = connections.get(key)
            if not isinstance(val, dict):
                logging.warn(f"Connection {key} skipped. Value must be a dictionary.")

            connection = session.query(Connection).filter_by(conn_id=key).first()
            if connection is not None:
                logging.info(f"Connection exists, skipping: {key}")
                continue

            logging.info("Setting connection: " + key)
            connection = Connection()
            connection.conn_id = key
            connection.conn_type = val.get("conn_type", None)
            connection.host = val.get("host", None)
            connection.schema = val.get("schema", None)
            connection.login = val.get("login", None)
            # connection._password=val.get("password", None)
            if "password" in val:
                connection.set_password(val.get("password") or "")
            connection.port = val.get("port", "80")
            if "extra" in val:
                extra = val.get("extra") or ""
                if extra is not None and not isinstance(extra, (int, str)):
                    extra = json.dumps(extra)
                connection.set_extra(extra)
            session.add(connection)

    config = {}
    for y in yamls:
        config.update(yaml.safe_load(y.format(**os.environ)) or {})

    load_variables(config=config)
    load_connections(config=config)
    load_pools(config=config)
