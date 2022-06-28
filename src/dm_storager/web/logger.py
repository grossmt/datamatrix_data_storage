import time

from loguru import logger

from dm_storager.utils.path import default_log_file

# configure logger
logger.add(default_log_file(), format="{message}")


# adjusted flask_logger
def flask_logger():
    """creates logging information"""
    with open(default_log_file()) as log_info:
        data = log_info.read()
        yield data.encode()
