import os
import socket

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

HOST_IP = os.getenv('SERVER_IP', local_ip)
HOST_PORT = os.getenv('SERVER_PORT', 50000)
