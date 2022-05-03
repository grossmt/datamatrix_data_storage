import logging
import json
from dataclasses import asdict, astuple
import toml

from typing import Optional, List, Union, List, NamedTuple
from pathlib import Path
from dm_storager.exceptions import ConfigNotExists

from dm_storager.structs import (
    Scanner,
    ScannerInfo,
    ScannerSettings,
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


def _resolve_scanner_settings(settings_path: Path) -> List[Scanner]:
    pass

    logger = configure_logger(__name__)

    if not settings_path.exists():
        logger.error(f"{str(settings_path)} file not found!")
        return []

    config_dict = toml.load(settings_path)
    scanners: List[Scanner] = []

    for client in config_dict["clients"]:

        info_scanner = ScannerInfo(
            name=config_dict["clients"][client]["name"],
            address=config_dict["clients"][client]["address"],
            scanner_id=config_dict["clients"][client]["id"],
            port=None,
        )

        scanner_settings = ScannerSettings(
            products=config_dict["clients"][client]["products"],
            server_ip=config_dict["clients"][client]["server_ip"],
            server_port=config_dict["clients"][client]["server_port"],
            gateway_ip=config_dict["clients"][client]["gateway_ip"],
            netmask=config_dict["clients"][client]["netmask"],
        )

        # logger.debug(f"Scanner info: {str(asdict(info_scanner))}")
        # logger.debug(f"Scanner settings: {str(asdict(scanner_settings))}")

        new_scanner = Scanner(
            info=info_scanner,
            settings=scanner_settings,
            queue=None,
            process=None,
            client_socket=None,
        )
        scanners.append(new_scanner)

    return scanners


# path = Path("settings") / "connection_settings.toml"

# l = _resolve_scanner_settings(path)

# pass