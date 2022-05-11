import os
import logging
import click

from logging.handlers import RotatingFileHandler

from dm_storager.utils.path import default_log_dir, default_log_file

kB = 1024  # noqa: N816
LOG_FILE_MAX_SIZE = 128 * kB  # noqa: WPS432

BACKUP_FILES_COUNT = 10


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
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",  # noqa: WPS323
        ),
    )

    # Setup file handler
    file_handler = RotatingFileHandler(
        filename=default_log_file(),
        mode="a",
        maxBytes=LOG_FILE_MAX_SIZE,
        backupCount=BACKUP_FILES_COUNT,
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",  # noqa: WPS323
        ),
    )

    root.addHandler(file_handler)
    root.addHandler(console_handler)
    root.name = "SERVER"

    return root


ROOT_LOGGER = get_root_logger()


def configure_logger(name: str, is_debug: bool = True) -> logging.Logger:
    logger = logging.getLogger(f"{ROOT_LOGGER.name}.{name}")
    logger.level = logging.DEBUG if is_debug else logging.INFO
    return logger
