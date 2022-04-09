import logging
import json

from typing import Optional, List, Union, List, NamedTuple
from pathlib import Path

from dm_storager.structs import (
    ScannerInfo,
)
from dm_storager.utils.logger import configure_logger

def resolve_scanners_settings(
    settings_path: Path,
) -> List[ScannerInfo]:

    logger = configure_logger(__name__)
    
    scanners: List[ScannerInfo] = []

    try:
        with open(settings_path, "r") as settings_file:
            scanners_json_settings = json.load(settings_file)
    except FileNotFoundError:
        logger.error(f"{str(settings_path)} file not found!")
        return []
    except json.JSONDecodeError as j_error:
        logger.error("An exception during json reading occurs:")
        logger.error(str(j_error))
        return []
    except Exception as ex:
        logger.error("An unhandled error during json reading occurs:")
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
