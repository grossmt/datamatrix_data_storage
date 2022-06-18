from pathlib import Path

BAD_PORT = 10048
BAD_HOST_ADDRESS = 10049


class Error(Exception):
    """Base server exception."""


class ConfigNotExists(Error):
    def __init__(self, config: Path) -> None:
        super().__init__(
            'Config file does not exist: "{config}"'.format(config=str(config))
        )


class ScannedIdNotRegistered(Error):
    def __init__(self, scanner_id: int) -> None:
        super().__init__(f"Scanner ID#{scanner_id} is not in registered scanner list!")


class ServerStop(Error):
    def __init__(self) -> None:
        super().__init__("Server stopped outside.")
