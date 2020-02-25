from sqlalchemy import Column, Integer, String, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from airflow.models.base import Base
from airflow.utils import timezone
from airflow.utils.sqlalchemy import UtcDateTime
from airflow.configuration import conf

SQL_ALCHEMY_SCHEMA = conf.get("core", "SQL_ALCHEMY_SCHEMA")
DB_LOGGER_SQL_ALCHEMY_SCHEMA = conf.get(
    "db_logger", "SQL_ALCHEMY_SCHEMA", fallback=SQL_ALCHEMY_SCHEMA
)

LoggerModelBase = declarative_base(
    metadata=(
        None
        if not SQL_ALCHEMY_SCHEMA or SQL_ALCHEMY_SCHEMA.isspace()
        else MetaData(schema=SQL_ALCHEMY_SCHEMA)
    )
)


class ExecutionLogRecord(LoggerModelBase):
    # FIXME: Not the base name for this table,
    # but since log was taken, it will have to do.
    # NOTE: This class is very similar to airflow.models.log,
    # but differs in purpose. Since we want
    # indexing to allow for fast log retrival, airflow.models.log
    # was not used.
    __tablename__ = "execution_log"

    id = Column(Integer, primary_key=True)
    dag_id = Column(String)
    task_id = Column(String)
    execution_date = Column(UtcDateTime)
    try_number = Column(Integer)
    text = Column(Text)

    __table_args__ = (
        Index("dag_id_idx", dag_id),
        Index("task_id_idx", task_id),
        Index("execution_date_idx", execution_date),
        Index("try_number_idx", try_number),
    )

    def __init__(
        self,
        dag_id: str,
        task_id: str,
        execution_date: datetime,
        try_number: int,
        text: str,
    ):
        super().__init__()

        self.dag_id = dag_id
        self.task_id = task_id
        self.execution_date = execution_date
        self.try_number = try_number
        self.text = text
