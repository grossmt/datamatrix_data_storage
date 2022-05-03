import time
import threading
import multiprocessing

from multiprocessing import Process, Queue
from typing import Tuple, List, Optional
from pathlib import Path
from dm_storager.exceptions import ServerStop

from dm_storager.protocol.exceptions import ProtocolMessageError
from dm_storager.protocol.packet_parser import get_scanner_id
from dm_storager.protocol.utils import format_bytestring
from dm_storager.utils.logger import configure_logger
from dm_storager.utils.scanner_network_settings_resolver import (
    _resolve_scanner_settings,
    resolve_scanners_settings,
)
from dm_storager.scanner_process import scanner_process
from dm_storager.server_queue import ServerQueue
from dm_storager.structs import (
    ClientMessage,
    HandshakeMessage,
    Scanner,
    ScannerInfo,
    ScannerSettings,
)


class Server:
    def __init__(self, ip: str, port: int, registred_clients_settings: Path) -> None:
        self._logger = configure_logger("ROOT_SERVER")

        self._queue = ServerQueue(ip, port, self._logger)
        self._registred_clients: List[ScannerInfo] = []
        self._scanners: List[Scanner] = []
        self._settings_path = registred_clients_settings

    @property
    def connection_info(self) -> Optional[Tuple[str, int]]:
        """Provides info about server ip and port.

        Returns:
            (str, int): IP-address and port of server.
        """
        if self._queue:
            return self._queue.server.server_address
        else:
            return None

    def init_server(self) -> None:
        """Init of server.

        Performs start of server thread and
        registration of allowed scanners from settings.
        """
        multiprocessing.set_start_method("spawn", force=True)

        self._queue.start_server()
        ip, port = self.connection_info
        self._logger.info("Server initialized:")
        self._logger.info(f"\tServer IP:   {ip}")
        self._logger.info(f"\tServer Port: {port}")

        self._register_scanners_from_settings()

    def stop_server(self) -> None:

        for scanner in self._scanners:

            if scanner.process and scanner.process.pid:
                self._logger.warning(
                    f"Scanner #{scanner.info.scanner_id}: killing process.",
                )
                scanner.process.kill()

        self._queue.server._is_running = False
        self._queue.server.shutdown()
        self._queue.server.server_close()

    def run_server(self) -> None:
        try:
            while True:
                time.sleep(0.1)
                while self._queue.exists():

                    message = self._queue.get()

                    if isinstance(message, ClientMessage):
                        self._handle_client_message(message)
                    elif isinstance(message, HandshakeMessage):
                        self._handle_handshake_message(message)

        except KeyboardInterrupt:
            self.stop_server()
            raise ServerStop

    def is_scanner_alive(self, scanner_id: int) -> bool:
        """Check is scanner alive.

        Args:
            scanner_id (int): id of scanner.

        Returns:
            bool: is scanner alive.
        """
        for scanner in self._scanners:
            if scanner.info.scanner_id == scanner_id and scanner.process.is_alive():
                return True
        return False

    def set_scanner_settings(self, scanner_id, settings: ScannerSettings) -> bool:
        for scanner in self._scanners:
            if scanner.info.scanner_id == scanner_id:
                if scanner.process.is_alive():
                    self._logger.info(
                        f"Applying new settings to scanner id #{scanner_id}..."
                    )
                else:
                    self._logger.warning(f"Scanner with id #{scanner_id} is not alive!")
                    self._logger.warning(
                        f"Settings will be apllied after scanner resurrection!"
                    )
                scanner.queue.put(settings)
                return True

        self._logger.error("No scanner with given ID found!")
        return False

    def _handle_handshake_message(self, handshake_message: HandshakeMessage):

        self._logger.debug("Got new connection!")
        self._logger.debug(f"\tClient IP:            {handshake_message.client_ip}")
        self._logger.debug(f"\tClient port:          {handshake_message.client_port}")

        if not self._is_client_registered(handshake_message.client_ip):
            self._logger.warning(
                f"Unregistred client connection from {handshake_message.client_ip}!"
            )
            handshake_message.client_socket.close()
            return

        for scanner in self._scanners:
            if scanner.info.address == handshake_message.client_ip:
                scanner.client_socket = handshake_message.client_socket
                scanner.queue = Queue()
                scanner.process = Process(target=scanner_process, args=(scanner,))

                try:
                    scanner.process.start()
                except AssertionError:
                    self._logger.warning(
                        f"Process for scanner {scanner.info.name}: ID#{scanner.info.scanner_id} was already started and killed due to error."
                    )
                    self._logger.warning("Restarting process...")
                    scanner.process = Process(
                        target=scanner_process,
                        args=(scanner,),
                    )
                    scanner.process.start()

                break

    def _handle_client_message(self, client_message: ClientMessage):
        self._logger.debug("Got new message!")
        self._logger.debug(f"\tClient IP:            {client_message.client_ip}")
        self._logger.debug(f"\tClient port:          {client_message.client_port}")

        try:
            scanner_id_int = get_scanner_id(client_message.client_message)
        except ProtocolMessageError as err:
            self._logger.error(str(err))
            return
        except Exception:
            self._logger.exception("Unhandled error:")
            self._logger.error(
                f"Raw message: {format_bytestring(client_message.client_message)}"
            )
            return

        if not self._is_scanner_id_registered(scanner_id_int):
            correct_id = 0
            for scanner in self._scanners:
                if client_message.client_ip == scanner.info.address:
                    correct_id = scanner.info.scanner_id
                    break
            self._logger.error(
                f"Client with address {client_message.client_ip} is registred, but has another ID: {correct_id}"
            )
            self._logger.error(
                f"Perhaps bad settings on {self._settings_path}, check it please."
            )
            self._logger.error(
                f"Skipped raw message: {format_bytestring(client_message.client_message)}"
            )
            return

        for scanner in self._scanners:
            if scanner_id_int == scanner.info.scanner_id:

                if scanner.process and scanner.process.is_alive():
                    scanner.queue.put(client_message.client_message)
                else:
                    try:
                        scanner.process.start()
                    except AssertionError:
                        self._logger.warning(
                            f"Process for scanner {scanner.info.name}: ID#{scanner.info.scanner_id} was already started and killed due to error."
                        )
                        self._logger.warning("Restarting process...")
                        scanner.process = Process(
                            target=scanner_process,
                            args=(scanner,),
                        )
                        scanner.process.start()
                break  # found given scanner, no need to iterate next

    def _is_client_registered(self, client_address: str) -> bool:
        for client in self._registred_clients:
            if client.address == client_address:
                return True
        return False

    def _is_scanner_id_registered(self, scanner_id: int) -> bool:
        return scanner_id in list(x.scanner_id for x in self._registred_clients)

    def _register_scanners_from_settings(self) -> None:
        scanners = _resolve_scanner_settings(self._settings_path)

        for scanner in scanners:
            self.register_single_scanner(scanner)

        self._logger.info(
            f"There are {len(self._registred_clients)} registred clients."
        )

    def register_single_scanner(self, scanner: Scanner) -> bool:
        """Performs registraion of a given scanner."""

        is_id_unique: bool = scanner.info.scanner_id in list(
            x.scanner_id for x in self._registred_clients
        )

        if not is_id_unique:
            self._registred_clients.append(scanner.info)
            self._logger.info("Registered scanner:")
            self._logger.info(f"\tScanner name:    {scanner.info.name}")
            self._logger.info(f"\tScanner address: {scanner.info.address}")
            self._logger.info(f"\tScanner id:      {scanner.info.scanner_id}")
            self._logger.info("\tScanner products:")
            for i in range(len(scanner.settings.products)):
                self._logger.info(f"\t\tProduct #{i}: {scanner.settings.products[i]}")
            self._logger.info(f"\tScanner server IP:    {scanner.settings.server_ip}")
            self._logger.info(f"\tScanner server port:  {scanner.settings.server_port}")
            self._logger.info(f"\tScanner gateway:      {scanner.settings.gateway_ip}")
            self._logger.info(f"\tScanner netmask:      {scanner.settings.netmask}")

            self._scanners.append(scanner)
            return True
        else:
            self._logger.error(
                f"Scanner with ID {scanner.info.scanner_id} already registred!"
            )
            return False