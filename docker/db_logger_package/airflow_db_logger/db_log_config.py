import os
import six
from airflow.configuration import conf
import logging

# initialize the execution log record table loader. Dose this work?
logging.warning("Adding tables for db logger")
from .execution_log_record import ExecutionLogRecord

# logging core params.
LOG_LEVEL = conf.get("core", "LOGGING_LEVEL").upper()
FAB_LOG_LEVEL = conf.get("core", "FAB_LOGGING_LEVEL").upper()
LOG_FORMAT = conf.get("core", "log_format")

# File logging.
BASE_LOG_FOLDER = conf.get("core", "BASE_LOG_FOLDER")
PROCESSOR_LOG_FOLDER = conf.get("scheduler", "child_process_log_directory")
FILENAME_TEMPLATE = "{{ ti.dag_id }}/{{ ti.task_id }}/{{ ts }}/{{ try_number }}.log"
PROCESSOR_FILENAME_TEMPLATE = "{{ filename }}.log"

# Logging with colors.
COLORED_LOG_FORMAT = conf.get("core", "COLORED_LOG_FORMAT")
COLORED_LOG = conf.getboolean("core", "COLORED_CONSOLE_LOG")
COLORED_FORMATTER_CLASS = conf.get("core", "COLORED_FORMATTER_CLASS")
FORMATTER_CLASS_KEY = "()" if six.PY2 else "class"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "airflow": {"format": LOG_FORMAT},
        "airflow_coloured": {
            "format": COLORED_LOG_FORMAT if COLORED_LOG else LOG_FORMAT,
            FORMATTER_CLASS_KEY: COLORED_FORMATTER_CLASS
            if COLORED_LOG
            else "logging.Formatter",
        },
    },
    "handlers": {
        "console": {
            "class": "airflow.utils.log.logging_mixin.RedirectStdHandler",
            "formatter": "airflow_coloured",
            "stream": "sys.stdout",
        },
        "task": {
            "class": "airflow_db_logger.db_log_handler.DBTaskLogHandler",
            "formatter": "airflow",
        },
        "processor": {
            "class": "airflow.utils.log.file_processor_handler.FileProcessorHandler",
            "formatter": "airflow",
            "base_log_folder": os.path.expanduser(PROCESSOR_LOG_FOLDER),
            "filename_template": PROCESSOR_FILENAME_TEMPLATE,
        },
    },
    "loggers": {
        "airflow.processor": {
            "handlers": ["processor"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "airflow.task": {"handlers": ["task"], "level": LOG_LEVEL, "propagate": False,},
        "flask_appbuilder": {
            "handler": ["console"],
            "level": FAB_LOG_LEVEL,
            "propagate": True,
        },
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL,},
}
