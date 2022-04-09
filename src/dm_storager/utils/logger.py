import logging

def get_root_logger() -> logging.Logger:

    logging.basicConfig(level=logging.DEBUG)

    root = logging.getLogger()
    if (root.hasHandlers()):
        root.handlers.clear()

    # Setup stderr handler
    console_handler = logging.StreamHandler()
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

    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",  # noqa: WPS323
        ),
    )

    root.addHandler(console_handler)
    root.addHandler(file_handler)    
    root.name = "SERVER"

    return root

ROOT_LOGGER = get_root_logger()

def configure_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"{ROOT_LOGGER.name}.{name}")
    return logger

