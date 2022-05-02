import argparse
import multiprocessing
from dm_storager.exceptions import ServerStop

from dm_storager.server import Server
from dm_storager.enviroment import HOST_IP, HOST_PORT, SCANNER_SETTINGS
from dm_storager.utils.logger import configure_logger


def main():

    parser = argparse.ArgumentParser("Datamatrix Storager")

    parser.add_argument("-v", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.set_defaults(v=False)

    args = parser.parse_args()
    is_verbose = args.v

    main_logger = configure_logger("SCANNER DATAMATRIX STORAGER", is_verbose)
    print("")

    server = Server(HOST_IP, HOST_PORT, SCANNER_SETTINGS)
    server.init_server()
    try:
        server.run_server()
    except ServerStop:
        main_logger.error("Stop server outside.")
        main_logger.error("Aborting program.")
    except Exception:
        main_logger.exception("Server runtime error:")
        server.stop_server()
        main_logger.error("Aborting program.")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
