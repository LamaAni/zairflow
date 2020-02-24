import sys
import logging


def init_logger():
    pass


def call_on_initdb():
    if "initdb" in sys.argv:
        logging.info("Command initdb invoked.")
        init_logger()

