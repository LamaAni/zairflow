import sys
import io
import os

from common import log, logging

# suppress stdout
sys.stdout = io.StringIO()
sys.stderr = io.StringIO()
logging.disable(logging.WARNING)
from airflow.configuration import conf


def get_config_value(combined_name: str):
    combined_name = combined_name.split(".")
    if len(combined_name) != 2:
        sys.__stderr__.write(
            "A config value name must be composed as: [section].[value]\n"
        )
        raise Exception("A config value name must be composed as: [section].[value]")

    val = conf.get(combined_name[0], combined_name[1], fallback="")
    return val


if __name__ == "__main__":
    combined_names = sys.argv[1:]
    values = []
    for combined_name in combined_names:
        values.append(get_config_value(combined_name))
    sys.__stdout__.write("\n".join(values))

