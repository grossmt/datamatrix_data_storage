import time
import multiprocessing

from multiprocessing import Process, Queue
from typing import Tuple, List
from pathlib import Path


from dm_storager.utils.logger import configure_logger

from dm_storager.utils.scanner_network_settings_resolver import (
    resolve_scanners_settings,
)
from dm_storager.scanner_process import scanner_process
from dm_storager.server_queue import ServerQueue
from dm_storager.structs import ClientMessage, Scanner, ScannerInfo


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

    def init_server(self) -> None:
        """Init of server.

        Performs start of server thread and
        registration of allowed scanners from settings.
        """
        multiprocessing.set_start_method("spawn", force=True)

        self._queue.start_server()
        ip, port = self.connection_info
        self._logger.info("Server initialized:")
        self._logger.info(f"Server IP:   {ip}")
        self._logger.info(f"Server Port: {port}")

        self._register_scanners_from_settings()

    def stop_server(self) -> None:
        self._logger.warning("Stopping server!")

        for scanner in self._scanners:
            self._logger.warning(
                f"Scanner #{scanner.info.scanner_id}: killing process."
            )
            scanner.process.kill()

        self._queue.stop_server()

    def run_server(self) -> None:
        while True:
            time.sleep(0.1)

            while self._queue.exists():
                self._handle_client_message(self._queue.get())

    def register_single_scanner(self, scanner_info: ScannerInfo) -> bool:
        """Performs registraion of a given scanner."""

        is_id_unique: bool = scanner_info.scanner_id in list(
            x.scanner_id for x in self._registred_clients
        )
        
        if not is_id_unique:
            self._registred_clients.append(scanner_info)
            self._logger.info("Registered scanner:")
            self._logger.info(f"\tScanner name:    {scanner_info.name}")
            self._logger.info(f"\tScanner address: {scanner_info.address}")
            self._logger.info(f"\tScanner id:      {scanner_info.scanner_id}")

            _q: Queue = Queue()

            new_scanner = Scanner(
                info=scanner_info,
                process=Process(target=scanner_process, args=(scanner_info, _q)),
                queue=_q,
            )
            self._scanners.append(new_scanner)
            return True
        else:
            self._logger.error(
                f"Scanner with ID {scanner_info.scanner_id} already registred!"
            )
            return False

    def is_scanner_alive(self, scanner_id: int) -> bool:
        for scanner in self._scanners:
            if scanner.info.scanner_id == scanner_id and scanner.process.is_alive():
                return True
        return False

    def set_scanner_settings(self, scanner_id, settings) -> bool:
        return False

    def _handle_client_message(self, client_message: ClientMessage):
        self._logger.debug("Got message!")
        self._logger.debug(f"\tClient IP:            {client_message.client_ip}")
        self._logger.debug(f"\tClient port:          {client_message.client_port}")
        self._logger.debug(f"\tClient raw message:   {client_message.client_message}")

        is_registered = self._is_client_registered(client_message.client_ip)

        if is_registered:

            try:
                scanner_id_int = int.from_bytes(
                    client_message.client_message[6:8], byteorder="big"
                )
            except Exception:
                self._logger.error("Bad scanner id")
                self._logger.error(f"Message: {client_message.client_message}")
                return

            for scanner in self._scanners:
                if scanner_id_int == scanner.info.scanner_id:
                    if scanner.process.is_alive():
                        scanner.queue.put(client_message.client_message)
                    else:
                        scanner.info.port = client_message.client_port
                        try:
                            scanner.process.start()
                        except AssertionError:
                            self._logger.warning(
                                f"Process for scanner {scanner.info.name}: ID#{scanner.info.scanner_id} was already started and killed due to error."
                            )
                            self._logger.warning("Restarting process...")
                            scanner.process = Process(
                                target=scanner_process,
                                args=(scanner.info, scanner.queue),
                            )
                            scanner.process.start()

                    break

        else:
            self._logger.warning(
                f"Unregistred scanner connection from {client_message.client_ip}!"
            )

    def _is_client_registered(self, client_address: str) -> bool:
        for client in self._registred_clients:
            if client.address == client_address:
                return True
        return False

    def _register_scanners_from_settings(self) -> None:
        clients = resolve_scanners_settings(self._settings_path)

        for client in clients:
            self.register_single_scanner(client)

        self._logger.info(
            f"There are {len(self._registred_clients)} registred clients."
        )
