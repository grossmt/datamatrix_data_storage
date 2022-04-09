import os
import socket

from pathlib import Path

hostname = socket.gethostname()
local_ips = socket.gethostbyname_ex(hostname)
local_ip = "127.0.0.1"
for ip in local_ips[2]:
    if "192.1" in ip:
        local_ip = ip
        break


HOST_IP = os.getenv("SERVER_IP", local_ip)
HOST_PORT = os.getenv("SERVER_PORT", 50000)

SCANNER_SETTINGS = os.getenv(
    "SCANNER_SETTINGS", Path("settings") / "connection_settings.json"
)
