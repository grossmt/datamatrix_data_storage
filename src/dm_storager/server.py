import time
import multiprocessing

from multiprocessing import Process, Queue
from typing import Tuple, List, Optional
from dm_storager.utils.logger import configure_logger

from dm_storager.utils.scanner_network_settings_resolver import (
    resolve_scanners_settings,
)
from dm_storager.scanner_process import scanner_process
from dm_storager.server_queue import ServerQueue
from dm_storager.structs import ClientMessage, Scanner, ScannerInfo

LOGGER = configure_logger("Server", True)


class Server:
    def __init__(self, ip: str, port: int) -> None:
        self._queue = ServerQueue(ip, port)
        self._scanners: List[Scanner] = []

        self._registred_clients: List[ScannerInfo] = []

    @property
    def connection_info(self) -> Tuple[str, int]:
        """Provides info about server ip and port.

        Returns:
            (str, int): IP-address and port of server.
        """

        return self._queue.server.server_address

    def init_server(self) -> None:
        self._queue.start_server()
        self._register_scanners_from_settings()

    def stop_server(self) -> None:
        self._queue.stop_server()

    def run_server(self) -> None:
        multiprocessing.set_start_method("spawn", force=True)

        # for scanner in self._scanners:
        #     scanner.process.start()

        while True:
            time.sleep(0.1)

            while self._queue.exists():
                self._handle_client_message(self._queue.get())

    def register_single_scanner(self, scanner_info: ScannerInfo):
        _q: Queue = Queue()
        new_scanner = Scanner(
            info=scanner_info,
            process=Process(target=scanner_process, args=(scanner_info, _q)),
            queue=_q,
        )
        self._scanners.append(new_scanner)

    def _handle_client_message(self, client_message: ClientMessage):
        LOGGER.info("Got message!")

        LOGGER.info(f"Client IP: {client_message.client_ip}")
        LOGGER.info(f"Client port: {client_message.client_port}")

        is_registered = self._is_client_registered(client_message.client_ip)

        if is_registered:

            try:
                scanner_id_str = client_message.client_message[6:8]
                scanner_id_int = int.from_bytes(
                    bytes(scanner_id_str, "utf-8"), byteorder="big"
                )
            except Exception:
                LOGGER.error("Bad scanner id")
                LOGGER.error(f"Message: {client_message.client_message}")
                return

            _q = self._get_scanner_queue(
                ScannerInfo(
                    address=client_message.client_ip,
                    port=client_message.client_port,
                    scanner_id=scanner_id_int,
                )
            )

            _q.put(client_message.client_message)

        else:
            LOGGER.warning(
                f"Unregistred scanner connection {client_message.client_ip} attempt!"
            )

    def _is_client_registered(self, client_address: str) -> bool:

        for client in self._registred_clients:
            if client.address == client_address:
                return True

        return False

    def _register_scanners_from_settings(self) -> Queue:
        self._registred_clients = resolve_scanners_settings()

    def _get_scanner_queue(self, new_scanner: ScannerInfo) -> None:
        """Get queue for process of scanner.

        If scanner process is running
        """
        for scanner in self._scanners:
            if scanner.info.address == new_scanner.address:
                return scanner.queue

        _q: Queue = Queue()
        new_scanner = Scanner(
            info=new_scanner,
            process=Process(target=scanner_process, args=(new_scanner, _q)),
            queue=_q,
        )
        self._scanners.append(new_scanner)

        # if self._scanners[-1].process.is_alive
        self._scanners[-1].process.start()

        return self._scanners[-1].queue
