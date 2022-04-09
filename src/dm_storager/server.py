import time
import multiprocessing

from multiprocessing import Process, Queue
from typing import Tuple, List, Optional
from pathlib import Path

from dm_storager.utils.logger import configure_logger

from dm_storager.utils.scanner_network_settings_resolver import (
    resolve_scanners_settings,
)
from dm_storager.scanner_process import scanner_process
from dm_storager.server_queue import ServerQueue
from dm_storager.structs import ClientMessage, Scanner, ScannerInfo

# LOGGER = configure_logger("Server", True)


class Server:
    def __init__(self, ip: str, port: int, registred_clients_settings: Path) -> None:
        self._queue = ServerQueue(ip, port)
        self._registred_clients: List[ScannerInfo] = []

        self._scanners: List[Scanner] = []

        self._settings_path = registred_clients_settings

        self._logger = configure_logger(__name__)

    @property
    def connection_info(self) -> Tuple[str, int]:
        """Provides info about server ip and port.

        Returns:
            (str, int): IP-address and port of server.
        """

        return self._queue.server.server_address

    # DONE
    def init_server(self) -> None:
        """Init of server.

        Performs start of server thread and
        registration of allowed scanners from settings.
        """
        multiprocessing.set_start_method("spawn", force=True)

        self._queue.start_server()
        self._register_scanners_from_settings()

    # DONE
    def register_single_scanner(self, scanner_info: ScannerInfo) -> None:
        """Performs registraion of a given scanner."""

        is_id_unique = scanner_info.scanner_id in list(
            x.scanner_id for x in self._registred_clients
        )
        if is_id_unique:
            self._registred_clients.append(scanner_info)
            self._logger.info("Registered scanner:")
            self._logger.info(f"Scanner name: {scanner_info.name}")
            self._logger.info(f"Scanner address: {scanner_info.address}")
            self._logger.info(f"Scanner id: {scanner_info.scanner_id}")

            _q: Queue = Queue()

            new_scanner = Scanner(
                info=scanner_info,
                process=Process(target=scanner_process, args=(scanner_info, _q)),
                queue=_q,
            )
            self._scanners.append(new_scanner)
            self._scanners[-1].process.start()

        else:
            self._logger.error(
                f"Scanner with ID {scanner_info.scanner_id} already registred!"
            )

    # DONE
    def stop_server(self) -> None:
        self._logger.warning("Stopping server!")

        for scanner in self._scanners:
            self._logger.warning(
                f"Scanner #{scanner.info.scanner_id}: killing process."
            )
            scanner.process.kill()

        self._queue.stop_server()

    # DONE
    def run_server(self) -> None:
        while True:
            time.sleep(0.1)

            while self._queue.exists():
                self._handle_client_message(self._queue.get())

    # DONE
    def _handle_client_message(self, client_message: ClientMessage):
        self._logger.info("Got message!")

        self._logger.info(f"Client IP: {client_message.client_ip}")
        self._logger.info(f"Client port: {client_message.client_port}")

        is_registered = self._is_client_registered(client_message.client_ip)

        if is_registered:

            try:
                scanner_id_str = client_message.client_message[6:8]
                scanner_id_int = int.from_bytes(
                    bytes(scanner_id_str, "utf-8"), byteorder="big"
                )
            except Exception:
                self._logger.error("Bad scanner id")
                self._logger.error(f"Message: {client_message.client_message}")
                return

            for scanner in self._scanners:
                if scanner_id_int == scanner.info.scanner_id:
                    scanner.queue.put(client_message.client_message)
                    break

        else:
            self._logger.warning(
                f"Unregistred scanner connection {client_message.client_ip} attempt!"
            )

    # DONE
    def _is_client_registered(self, client_address: str) -> bool:
        for client in self._registred_clients:
            if client.address == client_address:
                return True
        return False

    # DONE
    def _register_scanners_from_settings(self) -> None:
        clients = resolve_scanners_settings(self._settings_path)

        for client in clients:
            self.register_single_scanner(client)

        self._logger.info(
            f"There are {len(self._registred_clients)} registred clients."
        )
