from pathlib import Path
from typing import List, Optional, Tuple
import socket
import toml

from dm_storager.utils.logger import configure_logger

def resolve_local_addresses() -> List[str]:

    hostname = socket.gethostname()
    local_ips = socket.gethostbyname_ex(hostname)
    local_ip = "127.0.0.1"
    result = []
    for ip in local_ips[2]:
        result.append(ip)
    return[]
    
def create_new_default_settings(settings_path: Path) -> Path:
    
    return settings_path

def get_server_address(settings_path: Path) -> Tuple[Optional[str], Optional[int]]:
    
    _logger = configure_logger("SERVER SETTINGS CONFIGURATOR")
    
    _logger.debug(f"Resolving server connection address from {str(settings_path)}")

    if not settings_path.exists():
        _logger.error(f"{str(settings_path)} file not found!")
        sp = Path("settings") / "connection_settings.toml"
        _logger.info(f"Creating new file at {str(sp)}")
        
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