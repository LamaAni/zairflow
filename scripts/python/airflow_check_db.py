from common import log, ZARIFLOW_DB_WAIT_TRIES, ZARIFLOW_DB_WAIT_INTERVAL
from time import sleep

def airflow_db_ready():
    from sqlalchemy.orm import Session
    from airflow import settings
    from airflow.utils import db

    def check_db():
        with db.create_session() as session:
            db.check(session)

    last_ex = None
    for i in range(ZARIFLOW_DB_WAIT_TRIES):
        try:
            check_db()
            log.info("DB ready!")
            # flush log
            sleep(0.010)
            return True
        except Exception as ex:
            log.info(
                f"DB not ready, waiting {ZARIFLOW_DB_WAIT_INTERVAL} [s] before reattempt ({i}/{ZARIFLOW_DB_WAIT_TRIES})"
            )
            last_ex = ex
            sleep(ZARIFLOW_DB_WAIT_INTERVAL)

    raise Exception("Database not ready", last_ex)


if __name__ == "__main__":
    log.info("Checking database connection...")
    airflow_db_ready()
