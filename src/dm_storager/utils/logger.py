import logging

logging.basicConfig(
    level=logging.INFO,
)

LOGGER = logging.getLogger("Main Programm")
LOGGER.setLevel(logging.INFO)

def str_to_log_level(level: str, default: int = logging.DEBUG):
    """Convert log level name, ignoring case, to int representation."""
    return logging._nameToLevel.get(  # noqa: WPS437
        level.upper(),
        default,
    )

def configure_root_logger(name: str, is_verbose: bool) -> logging.Logger:
    root = logging.getLogger()

    if is_verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    # Setup stderr handler
    # stderr_handler = logging.StreamHandler()
    # stderr_handler.setLevel(log_level)
    # stderr_handler.setFormatter(
    #     logging.Formatter(
    #         "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",  # noqa: WPS323
    #     ),
    # )
    # root.addHandler(stderr_handler)

    root.setLevel(log_level)
    root.name = name
    

    return root