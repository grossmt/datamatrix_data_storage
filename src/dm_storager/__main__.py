import logging

from dm_storager.server import Server
from dm_storager.enviroment import HOST_IP, HOST_PORT

logging.basicConfig(
    level=logging.INFO,
)

LOGGER = logging.getLogger("Main Programm")
LOGGER.setLevel(logging.INFO)


if __name__ == "__main__":

    server = Server(HOST_IP, HOST_PORT)
    ip, port = server.connection_info

    LOGGER.info(f"Server address: {ip}")
    LOGGER.info(f"Server port: {port}")

    server.start_server()

    try:
        server.run_server()
    except Exception:
        LOGGER.exception("Server runtime error:")
        server.stop_server()
        exit(0)
