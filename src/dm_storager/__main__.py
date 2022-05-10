from dm_storager.cli import entry_point as main

import argparse

from pathlib import Path

from dm_storager.server import Server
from dm_storager.enviroment import SCANNER_SETTINGS
from dm_storager.utils.logger import configure_logger

from dm_storager.exceptions import ServerStop


def _main():

    main_logger = configure_logger("SCANNER DATAMATRIX STORAGER", is_verbose)

    server = Server()

    if server.is_configured:
        pass
        # ready to init and run
    else:
        pass
        # must fill settings file

    server.preconfigure_server(Path(SCANNER_SETTINGS))
    server.init_server()

    try:
        server.run_server()

    except ServerStop:
        main_logger.error("Stop server outside.")
        main_logger.error("Aborting program.")
    except Exception:
        main_logger.exception("Server runtime error:")
        server.stop_server()

    if server_ip and server_port:

        try:
            server = Server(server_ip, server_port, SCANNER_SETTINGS)
        except OSError as ex:
            main_logger.error("Bad server connection settings:")
            if ex.errno == 10049:
                main_logger.error(f"Bad server IP")
            if ex.errno == 10048:
                main_logger.error(f"Bad server port")

            main_logger.error(f"Resolved Server IP:   {server_ip}")
            main_logger.error(f"Resolved Server Port: {server_port}")

            return False

        server.init_server()
        try:
            server.run_server()
        except ServerStop:
            main_logger.error("Stop server outside.")
            main_logger.error("Aborting program.")
        except Exception:
            main_logger.exception("Server runtime error:")
            server.stop_server()
            return False
    else:
        main_logger.error("Could not start server.")
        return False


if __name__ == "__main__":
    main()
