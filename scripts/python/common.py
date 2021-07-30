import os
import sys
import logging

LOG_LEVEL = os.environ.get("LOG_LEVEL", logging.INFO)
ZARIFLOW_DB_WAIT_TRIES = int(os.environ.get("ZARIFLOW_DB_WAIT_TRIES", "60"))
ZARIFLOW_DB_WAIT_INTERVAL = int(os.environ.get("ZARIFLOW_DB_WAIT_INTERVAL", "1"))

log = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.__stdout__)
handler.formatter = logging.Formatter(fmt="[%(asctime)s][zairflow][%(levelname)7s] %(message)s")
log.addHandler(handler)
log.setLevel(LOG_LEVEL)
