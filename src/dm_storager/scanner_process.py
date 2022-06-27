import sys

from dm_storager.scanner_handler import ScannerHandler
from dm_storager.structs import Scanner, ScannerSettings


def scanner_process(
    scanner_id: str, scanner_dict: ScannerSettings, is_debug: bool = False
):
    # Serialize dict item to dataclass
    scanner = Scanner(
        scanner_id=scanner_id,
        info=scanner_dict["info"],  # type: ignore
        settings=scanner_dict["settings"],  # type: ignore
        runtime=scanner_dict["runtime"],  # type: ignore
    )

    scanner_handler = ScannerHandler(scanner, is_debug)

    if scanner_handler.is_alive:
        scanner_handler.run_process()
    else:
        scanner_handler._logger.error(
            "Failed to initialize scanner handler in process."
        )

    del scanner_handler

    sys.exit()
