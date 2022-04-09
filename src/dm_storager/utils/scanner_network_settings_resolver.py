import logging
import json

from typing import Optional, List, Union, List, NamedTuple
from pathlib import Path

from dm_storager.structs import (
    ScannerInfo,
)


class ValidationResult(NamedTuple):
    result: bool
    msg: str


# def is_valid_scanner_info(scanner: ScannerStat) -> ValidationResult:

#     r = ValidationResult(result=True, msg="")
#     return r
#     # r.result = True
#     # r.msg = ""


LOGGER = logging.getLogger("Server")
LOGGER.setLevel(logging.INFO)


def resolve_scanners_settings(
    settings_path: Path,
) -> List[ScannerInfo]:

    LOGGER.info(f"Resolving settings of scanners from {str(settings_path)}")

    scanners: List[ScannerInfo] = []

    try:
        with open(settings_path, "r") as settings_file:
            scanners_json_settings = json.load(settings_file)
    except FileNotFoundError:
        LOGGER.error(f"{str(settings_path)} file not found!")
        return []
    except json.JSONDecodeError as j_error:
        LOGGER.error("An exception during json reading occurs:")
        LOGGER.error(str(j_error))
        return []
    except Exception as ex:
        LOGGER.error("An unhandled error during json reading occurs:")
        print(str(ex))
        return []

    for record in scanners_json_settings["scanners"]:
        new_scanner = ScannerInfo(
            name=record["name"],
            address=record["address"],
            port=None,
            scanner_id=record["id"],
        )
        scanners.append(new_scanner)

    return scanners
