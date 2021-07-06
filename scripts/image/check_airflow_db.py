import logging
from sqlalchemy.orm import Session


def airflow_is_db_ready():
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


if __name__ == "__main__":
    airflow_is_db_ready()

