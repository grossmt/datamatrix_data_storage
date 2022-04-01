import argparse

from dm_storager.server import Server
from dm_storager.enviroment import HOST_IP, HOST_PORT
from dm_storager.utils.logger import configure_logger


if __name__ == "__main__":

    parser = argparse.ArgumentParser("Datamatrix Storager")

    parser.add_argument("-v", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.set_defaults(v=False)
    args = parser.parse_args()
    is_verbose = args.v

    server = Server(HOST_IP, HOST_PORT)

    ip, port = server.connection_info

    main_logger = configure_logger("SCANNER DATAMATRIX STORAGER", is_verbose)

    print("")
    main_logger.info(f"Server address: {ip}")
    main_logger.info(f"Server port: {port}")

    server.init_server()
    try:
        server.run_server()
    except Exception:
        main_logger.exception("Server runtime error:")
        server.stop_server()
        main_logger.error("Aborting program.")
        exit(0)
