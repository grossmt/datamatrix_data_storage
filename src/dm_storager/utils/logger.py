import logging

# logging.basicConfig(
#     level=logging.INFO,
# )

# LOGGER = logging.getLogger("Main Programm")
# LOGGER.setLevel(logging.INFO)


def str_to_log_level(level: str, default: int = logging.DEBUG):
    """Convert log level name, ignoring case, to int representation."""
    return logging._nameToLevel.get(  # noqa: WPS437
        level.upper(),
        default,
    )


def configure_logger(name: str, is_verbose: bool = False) -> logging.Logger:

    log_level = logging.DEBUG if is_verbose else logging.INFO

    logging.basicConfig(level=log_level)

    root = logging.getLogger()

    # Setup stderr handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",  # noqa: WPS323
        ),
    )
    # Setup file handler
    try:
        file_handler = logging.FileHandler(filename="logs/server_log")
    except FileNotFoundError:
        pass

    file_handler.setLevel(log_level)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",  # noqa: WPS323
        ),
    )

    root.addHandler(console_handler)
    root.addHandler(file_handler)

    root.name = name

    return root