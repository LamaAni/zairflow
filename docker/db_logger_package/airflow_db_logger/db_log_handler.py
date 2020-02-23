import logging

import yaml
from airflow.utils.helpers import parse_template_string
from airflow.models import TaskInstance
from airflow.utils.db import provide_session
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, Index, DateTime
from airflow.models.base import Base
from typing import Dict, List


class ExecutionLogTaskContextInfo:
    def __init__(self, task_instance: TaskInstance):
        super().__init__()
        self.dag_id = task_instance.dag_id
        self.task_id = task_instance.task_id
        self.execution_date = task_instance.execution_date
        self.try_number = task_instance.tr


class ExecutionLogRecord(Base):
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
    execution_date = Column(DateTime)
    try_number = Column(Integer)
    text = Column(Text)

    __table_args__ = (
        Index("dag_id_idx", dag_id),
        Index("task_id_idx", task_id),
        Index("execution_date_idx", execution_date),
        Index("try_number_idx", try_number),
    )

    def __init__(self, task_context_info: ExecutionLogTaskContextInfo, text: str):
        super().__init__()

        self.dag_id = task_context_info.dag_id
        self.task_id = task_context_info.task_id
        self.execution_date = task_context_info.execution_date
        self.try_number = task_context_info.tr


class DBTaskLogHandler(logging.Handler):
    """
    DB Task log handler writes and reads task logs from the logging database
    (Defaults to the airflow database, unless otherwise defined)
    """

    _task_context_info: TaskInstance = None

    def __init__(self):
        super().__init__()
        self._task_context_info = None

    @property
    def task_context_info(self):
        assert (
            self._task_context_info is not None
        ), "Task instance was not defined while attempting to write task log"
        return self._task_context_info

    def set_context(self, task_instance):
        """Initialize the db log configuration.
        
        Arguments:
            task_instance {task instance objecct} -- The task instace to write for.
        """
        self._task_context_info = ExecutionLogTaskContextInfo(task_instance)

    @provide_session
    def emit(self, record, session: Session):
        """Emits a log record.
        
        Arguments:
            record {any} -- The logging record.
        """

        db_record = ExecutionLogRecord(
            self.task_context_info, record if isinstance(record, str) else yaml.safe_dump(record)
        )
        session.add(db_record)

    @provide_session
    def flush(self, session):
        """Waits for any unwritten logs to write to the db.
        """
        session.flush()

    def close(self):
        """Stops and finalizes the log writing.
        """
        # nothing to, the session is handled by the reader.
        pass

    @provide_session
    def read(
        self,
        task_instance: TaskInstance,
        session: Session,
        try_number: int = None,
        metadata: dict = None,
    ):
        """Read logs of given task instance from the database.
        
        Arguments:
            task_instance {TaskInstance} -- The task instance object
            session {Session} -- The db session object.
        
        Keyword Arguments:
            try_number {int} -- The run try number (default: {None})
            metadata {dict} -- Added metadata (default: {None})
        
        Raises:
            Exception: [description]
        
        Returns:
            List[str] -- A log array.
        """
        # Task instance increments its try number when it starts to run.
        # So the log for a particular task try will only show up when
        # try number gets incremented in DB, i.e logs produced the time
        # after cli run and before try_number + 1 in DB will not be displayed.

        if try_number is None:
            next_try = task_instance.next_try_number
            try_numbers = list(range(1, next_try))
        elif try_number < 1:
            logs = [
                "Error fetching the logs. Try number {} is invalid.".format(try_number),
            ]
            return logs
        else:
            try_numbers = [try_number]

        logs = [""] * len(try_numbers)
        logs_by_try_number = Dict[int, List[ExecutionLogRecord]]

        log_records = (
            session.query(ExecutionLogRecord)
            .filter(ExecutionLogRecord.dag_id == self.task_context_info.dag_id)
            .filter(ExecutionLogRecord.task_id == self.task_context_info.task_id)
            .filter(ExecutionLogRecord.execution_date == self.task_context_info.execution_date)
            .filter(ExecutionLogRecord.try_number.in_(try_numbers))
            .all()
        )

        for log_record in log_records:
            try_number = int(log_record.try_number)
            if try_number not in logs_by_try_number:
                logs_by_try_number[try_number] = []
            logs_by_try_number[try_number].append(log_record)

        for try_number in logs_by_try_number.keys():
            try_records = logs_by_try_number[try_numbers]
            if try_number < 0 or try_number >= len(try_numbers):
                continue
            try_log_lines = [str(record.text) for record in try_records]
            string_log = "\n".join(try_log_lines)
            logs[try_number] = string_log

        return logs

