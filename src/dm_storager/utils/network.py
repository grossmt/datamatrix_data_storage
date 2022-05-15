import socket
from typing import List

MIN_PORT_NUMBER = 1024
MAX_PORT_NUMBER = 65536


def resolve_local_addresses() -> List[str]:

    hostname = socket.gethostname()
    local_ips = socket.gethostbyname_ex(hostname)
    result = []
    for ip in local_ips[2]:
        result.append(ip)
    return result