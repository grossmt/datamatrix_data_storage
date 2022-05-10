from pathlib import Path
from typing import Dict, List, Optional, Tuple
import socket
import toml
from dm_storager.structs import Scanner, ScannerInfo, ScannerSettings

from dm_storager.utils.logger import configure_logger


def resolve_local_addresses() -> List[str]:

    hostname = socket.gethostname()
    local_ips = socket.gethostbyname_ex(hostname)
    local_ip = "127.0.0.1"
    result = []
    for ip in local_ips[2]:
        result.append(ip)
    return result


def create_new_default_settings(settings_path: Path) -> Path:

    server_settings: Dict = {"address": "", "port": 0}

    print("Resolved local interfaces:")
    ips = resolve_local_addresses()
    for ip in ips:
        print(f"[{ips.index(ip)}]: {ip}")

    # client_settings: Dict = {

    # }

    _info = ScannerInfo(
        name="Scanner name", address="Enter scanner address", scanner_id=0, port=0
    )

    _settings = ScannerSettings(
        products=list("" for i in range(6)),
        server_ip="Enter server IP",
        server_port=0,
        gateway_ip="Enter gateway IP",
        netmask="Enter gateway mask",
    )

    default_scanner_settings = Scanner()

    return settings_path


def get_server_address(settings_path: Path) -> Tuple[Optional[str], Optional[int]]:

    _logger = configure_logger("SERVER SETTINGS CONFIGURATOR")

    _logger.debug(f"Resolving server connection address from {str(settings_path)}")

    if not settings_path.exists():
        _logger.error(f"{str(settings_path)} file not found!")
        # sp = Path("settings") / "connection_settings.toml"
        _logger.info(f"Creating new file at {str(settings_path)}")

        try:
            sp = create_new_default_settings(sp)
        except Exception as ex:
            _logger.error(str(ex))
    else:
        # settings path exist
        config_dict = toml.load(settings_path)

        try:
            server_settings = config_dict["server"]
            server_ip = server_settings["address"]
            server_port = server_settings["port"]

            return (str(server_ip), int(server_port))
        except KeyError as ex:
            if ex.args[0] == "server":
                # no settings for server
                pass
            if ex.args[0] == "address":
                # no settings for server
                pass
            if ex.args[0] == "port":
                # no settings for server
                pass

            pass

    return (None, None)
