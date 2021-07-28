import logging
import os
from time import sleep

ZARIFLOW_DB_WAIT_TRIES = int(os.environ.get("ZARIFLOW_DB_WAIT_TRIES", "60"))
ZARIFLOW_DB_WAIT_INTERVAL = int(os.environ.get("ZARIFLOW_DB_WAIT_INTERVAL", "60"))


def airflow_is_db_ready():
    max_check_count = os.environ.get("")
    try:
        from airflow import settings
        from airflow.utils import db
        from airflow.models import Log

        logging.info("Checking database connection...")
        with db.create_session() as session:
            db.check(session)
            logging.info("Checking database structure...")
            session.query(Log).limit(0).count()
    except Exception as err:
        raise Exception("Airflow db not ready, log table dose not exist.", err)

    logging.info("DB ready")


def airflow_db_ready():
    from sqlalchemy.orm import Session
    from airflow import settings
    from airflow.utils import db

    def check_db():
        logging.info("Checking database connection...")
        with db.create_session() as session:
            db.check(session)

    last_ex = None
    for i in range(ZARIFLOW_DB_WAIT_TRIES):
        try:
            check_db()
            logging.info("DB ready!")
            return True
        except Exception as ex:
            last_ex = ex
            sleep(ZARIFLOW_DB_WAIT_INTERVAL)

    raise Exception("Database not ready", last_ex)


if __name__ == "__main__":
    airflow_db_ready
