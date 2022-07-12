import sys
from pathlib import Path

from dm_storager.scanner_handler import ScannerHandler
from dm_storager.structs import Scanner, ScannerSettings
from dm_storager.utils.path import default_data_folder


def scanner_process(
    scanner_id: str,
    scanner_dict: ScannerSettings,
    is_debug: bool = False,
    data_path: Path = default_data_folder(),
):
    # Serialize dict item to dataclass
    scanner = Scanner(
        scanner_id=scanner_id,
        info=scanner_dict["info"],  # type: ignore
        settings=scanner_dict["settings"],  # type: ignore
        runtime=scanner_dict["runtime"],  # type: ignore
    )

    scanner_handler = ScannerHandler(scanner, data_path, is_debug)

    if scanner_handler.is_alive:
        scanner_handler.run_process()
    else:
        scanner_handler._logger.error(
            "Failed to initialize scanner handler in process."
        )

    del scanner_handler

    sys.exit()
