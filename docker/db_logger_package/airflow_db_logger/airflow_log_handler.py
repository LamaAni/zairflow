import logging

import sys
import yaml
from airflow.utils.helpers import parse_template_string
from airflow.models import TaskInstance
from sqlalchemy import Column, Integer, String, Text, Index, DateTime
from airflow.models.base import Base
from typing import Dict, List

from .execution_log_record import ExecutionLogRecord
from .logger_config import Session
import logging


class ExecutionLogTaskContextInfo:
    def __init__(self, task_instance: TaskInstance):
        super().__init__()
        self.dag_id = task_instance.dag_id
        self.task_id = task_instance.task_id
        self.execution_date = task_instance.execution_date
        self.try_number = task_instance.try_number


class DBTaskLogHandler(logging.Handler):
    """
    DB Task log handler writes and reads task logs from the logging database
    (Defaults to the airflow database, unless otherwise defined)
    """

    _task_context_info: TaskInstance = None
    _db_session: Session = None

    def __init__(self):
        super().__init__()
        self._task_context_info = None
        self._db_session = None

    @property
    def task_context_info(self):
        assert (
            self._task_context_info is not None
        ), "Task instance was not defined while attempting to write task log"
        return self._task_context_info

    @property
    def has_context(self):
        return self._task_context_info is not None

    @property
    def db_session(self) -> Session:
        return self._db_session

    def set_context(self, task_instance):
        """Initialize the db log configuration.
        
        Arguments:
            task_instance {task instance object} -- The task instace to write for.
        """
        logging.warn("Setting session context")

        try:
            self._task_context_info = ExecutionLogTaskContextInfo(task_instance)
            self._db_session = Session()
        except Exception as err:
            logging.error(err)

    def emit(self, record):
        """Emits a log record.
        
        Arguments:
            record {any} -- The logging record.
        """
        if not self.has_context:
            return

        db_record = ExecutionLogRecord(
            self.task_context_info.dag_id,
            self.task_context_info.dag_id,
            self.task_context_info.execution_date,
            self.task_context_info.try_number,
            self.format(record),
        )

        self.db_session.add(db_record)
        self.db_session.commit()

    def flush(self):
        """Waits for any unwritten logs to write to the db.
        """
        if not self.has_context:
            return
        if self.db_session is not None:
            self.db_session.flush()

    def close(self):
        if not self.has_context:
            return
        """Stops and finalizes the log writing.
        """
        if self.db_session is not None:
            self.db_session.close()

    def read(
        self,
        task_instance: TaskInstance,
        try_number: int = None,
        metadata: dict = None,
    ):
        """Read logs of given task instance from the database.
        
        Arguments:
            task_instance {TaskInstance} -- The task instance object
        
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

        try:
            if try_number is None:
                next_try = task_instance.next_try_number
                try_numbers = list(range(1, next_try))
            elif try_number < 1:
                logs = [
                    "Error fetching the logs. Try number {} is invalid.".format(
                        try_number
                    ),
                ]
                return logs
            else:
                try_numbers = [try_number]

            logs = [""] * len(try_numbers)
            metadata_array = [{}] * len(try_numbers)
            logs_by_try_number = Dict[int, List[ExecutionLogRecord]]

            with Session() as db_session:
                log_records = (
                    db_session.query(ExecutionLogRecord)
                    .filter(ExecutionLogRecord.dag_id == task_instance.dag_id)
                    .filter(ExecutionLogRecord.task_id == task_instance.task_id)
                    .filter(
                        ExecutionLogRecord.execution_date
                        == task_instance.execution_date
                    )
                    .filter(ExecutionLogRecord.try_number.in_(try_numbers))
                    .all()
                )

            logging.warning("Log records found: " + str(len(log_records)))

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
                metadata_array[try_number] = {"end_of_log": True}

            return logs, metadata_array
        except Exception as err:
            logging.error(err)
            logging.error("Failed to read log from db")

