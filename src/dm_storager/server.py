import time
import multiprocessing

from multiprocessing import Process, Queue
from typing import Tuple, List
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

        for scanner in self._scanners:
            scanner.process.start()

        while True:
            time.sleep(0.1)

            while self._queue.exists():
                self._handle(self._queue.get())

    def _handle(self, client_message: ClientMessage):
        LOGGER.info("Got message!")

        LOGGER.info(f"Client IP: {client_message.client_ip}")
        LOGGER.info(f"Client port: {client_message.client_port}")

        try:
            scanner_id_str = client_message.client_message[6:8]
            scanner_id_int = int.from_bytes(
                bytes(scanner_id_str, "utf-8"), byteorder="big"
            )

        except Exception:
            LOGGER.error("Bad scanner id")
            LOGGER.error(f"Message: {client_message.client_message}")
            return

        for scanner in self._scanners:
            if scanner._info.scanner_id == scanner_id_int:
                scanner._queue.put(client_message.client_message)
                return

        LOGGER.error(f"Got message from unregistred scanner: {scanner_id_int}")

    def register_single_scanner(self, scanner_info: ScannerInfo):
        _q: Queue = Queue()
        new_scanner = Scanner(
            info=scanner_info,
            process=Process(target=scanner_process, args=(scanner_info, _q)),
            queue=_q,
        )
        self._scanners.append(new_scanner)

    def _register_scanners_from_settings(self) -> None:

        scanners_info_list = resolve_scanners_settings()
        assert scanners_info_list is not None

        for record in scanners_info_list:

            _q: Queue = Queue()
            new_scanner = Scanner(
                info=record,
                process=Process(target=scanner_process, args=(record, _q)),
                queue=_q,
            )
            self._scanners.append(new_scanner)
