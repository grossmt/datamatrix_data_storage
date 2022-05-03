import argparse
import multiprocessing

from dm_storager.server import Server
from dm_storager.enviroment import SCANNER_SETTINGS, HOST_IP, HOST_PORT
from dm_storager.utils.logger import configure_logger
from dm_storager.utils.network_settings import get_server_address

from dm_storager.exceptions import ServerStop


def main() -> bool:

    parser = argparse.ArgumentParser("Datamatrix Storager")

    parser.add_argument("-v", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.set_defaults(v=False)

    args = parser.parse_args()
    is_verbose = args.v

    main_logger = configure_logger("SCANNER DATAMATRIX STORAGER", is_verbose)
    print("")

    server_ip, server_port = get_server_address(SCANNER_SETTINGS)
    
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
    multiprocessing.freeze_support()
    should_restart = True

    while should_restart:
        should_restart = main()
        
    print("Aborting program.")
