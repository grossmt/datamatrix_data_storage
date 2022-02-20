from pathlib import Path
from sys import byteorder
import time
import asyncio
import logging

from json import JSONDecodeError

from dm_storager.SocketListener import SocketHandler
from dm_storager.structs import StateControlPacket, ScannerStat

from dm_storager.json_parser import scanners_settings_reading, is_valid_scanner_info

from dm_storager.const import SCANNER_SETTINGS

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


def main(settings_path: Path = SCANNER_SETTINGS):
    LOGGER.info("Start of programm")

    try:
        scanners_json_settings = scanners_settings_reading(SCANNER_SETTINGS)
    except FileNotFoundError:
        LOGGER.error(f"{str(settings_path)} file not found!")
        LOGGER.error("Closing app.")
        exit(0)
    except JSONDecodeError as j_error:
        LOGGER.error("An exception during json reading occurs:")
        LOGGER.error(str(j_error))
        exit(0)
    except Exception as ex:
        LOGGER.error("An unhandled error during json reading occurs:")
        print(str(ex))
        LOGGER.error("Closing app.")
        exit(0)

    scanners_handler = SocketHandler()

    for record in scanners_json_settings["scanners"]:

        scanner = ScannerStat(
            address=record["address"],
            port=record["port"],
            scanner_id=record["id"],
        )
        validation_result = is_valid_scanner_info(scanner)
        if validation_result.result:
            scanners_handler.add_scanner(scanner)
        else:
            LOGGER.error("Scanner info is not valid!")
            LOGGER.error(f"Reason: {validation_result.msg}")

    for scanner in scanners_handler._scanners_handlers:
        asyncio.run(scanners_handler.run_scanner(scanner))

    while True:
        pass
    
if __name__ == "__main__":
    main()
