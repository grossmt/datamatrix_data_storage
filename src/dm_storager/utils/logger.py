import os
import logging
import click

from concurrent_log_handler import ConcurrentRotatingFileHandler

from dm_storager.utils.path import default_log_dir, default_log_file

kB = 1024  # noqa: N816
LOG_FILE_MAX_SIZE = 256 * kB  # noqa: WPS432

BACKUP_FILES_COUNT = 10

LOG_FORMAT = "%(asctime)s : %(name)-12s : %(levelname)-8s %(message)s"


class ColorizedFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: grey + LOG_FORMAT + reset,
        logging.INFO: green + LOG_FORMAT + reset,
        logging.WARNING: yellow + LOG_FORMAT + reset,
        logging.ERROR: red + LOG_FORMAT + reset,
        logging.CRITICAL: bold_red + LOG_FORMAT + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def get_root_logger(is_debug: bool = False) -> logging.Logger:
    """Creates root logger with console and file output.

    Arguments:
        is_debug (bool): set log level to debug if true

    Raises:
        OSError: can not create dir with logs
    """

    try:
        os.makedirs(default_log_dir(), exist_ok=True)
    except OSError:
        click.echo("Failed to create directory with logs.")
        click.echo("Please be sure you have permissions on this directory.")
        raise OSError

    logging.basicConfig(level=logging.DEBUG if is_debug else logging.INFO)

    root = logging.getLogger()
    if root.hasHandlers():
        root.handlers.clear()

    # Setup stderr console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorizedFormatter())

    # Setup file handler
    file_handler = ConcurrentRotatingFileHandler(
        filename=default_log_file(),
        mode="a",
        maxBytes=LOG_FILE_MAX_SIZE,
        backupCount=BACKUP_FILES_COUNT,
    )

    file_handler.setFormatter(
        logging.Formatter(LOG_FORMAT),
    )

    root.addHandler(file_handler)
    root.addHandler(console_handler)
    root.name = "DM_STORAGER"

    return root


ROOT_LOGGER = get_root_logger()


def configure_logger(name: str, is_debug: bool = True) -> logging.Logger:
    logger = logging.getLogger(f"{ROOT_LOGGER.name}.{name}")
    logger.level = logging.DEBUG if is_debug else logging.INFO
    return logger
