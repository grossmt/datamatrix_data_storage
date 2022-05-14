import time
import multiprocessing
from multiprocessing import Process, Queue
from typing import Tuple, List, Optional

from dm_storager import Config
from dm_storager.exceptions import BAD_HOST_ADDRESS, BAD_PORT, ServerStop
from dm_storager.protocol.exceptions import ProtocolMessageError
from dm_storager.protocol.packet_parser import get_scanner_id
from dm_storager.protocol.utils import format_bytestring
from dm_storager.utils.logger import configure_logger

from dm_storager.scanner_process import scanner_process
from dm_storager.server_queue import ServerQueue
from dm_storager.structs import (
    ClientMessage,
    HandshakeMessage,
    Scanner,
    ScannerInfo,
    ScannerInternalSettings,
    ScannerRuntimeSettings,
    ScannerSettings,
)


class Server:
    def __init__(self, config: Config, debug: bool) -> None:
        self._logger = configure_logger("ROOT_SERVER", debug)
        self._queue: Optional[ServerQueue] = None
        self._config: Config = config

        self._is_configured = self._configure_server()

    @property
    def is_configured(self) -> bool:
        return self._is_configured

    @property
    def connection_info(self) -> Tuple[str, int]:
        """Provides info about server ip and port.

        Returns:
            (str, int): IP-address and port of server.
        """
        return (self._config.server.host, self._config.server.port)

    def _configure_server(self) -> bool:

        # validate connection pair
        try:
            self._queue = ServerQueue(
                self._config.server.host, self._config.server.port, self._logger
            )
            self._queue.start_server()
        except OSError as ex:
            self._logger.error("Bad server connection settings:")
            if ex.errno == BAD_PORT:
                self._logger.error("Bad server port.")
            if ex.errno == BAD_HOST_ADDRESS:
                self._logger.error("Bad server IP.")

            self._logger.error(f"Resolved Server IP:     {self._config.server.host}")
            self._logger.error(f"Resolved Server port:   {self._config.server.port}")

            return False

        multiprocessing.set_start_method("spawn", force=True)

        ip, port = self.connection_info
        self._logger.info("Server initialized:")
        self._logger.info(f"\tServer IP:   {ip}")
        self._logger.info(f"\tServer Port: {port}")

        for scanner in self._config.scanners:
            self._emit_debug_scanner_info(scanner, self._config.scanners[scanner])

        self._logger.info(f"There are {len(self._config.scanners)} registred clients.")
        return True

    def run_server(self) -> None:
        try:
            while True:
                time.sleep(0.1)
                while self._queue.exists():  # type: ignore

                    message = self._queue.get()  # type: ignore
                    if isinstance(message, HandshakeMessage):
                        self._handle_handshake_message(message)
                    elif isinstance(message, ClientMessage):
                        self._handle_client_message(message)

        except KeyboardInterrupt:
            self.stop_server()
            raise ServerStop

    def stop_server(self) -> None:
        # for scanner in self._scanners:
        #     if scanner.process and scanner.process.pid:
        #         self._logger.warning(
        #             f"Scanner #{scanner.info.scanner_id}: killing process.",
        #         )
        #         scanner.process.kill()

        self._queue.server.is_running = False  # type: ignore
        self._queue.server.shutdown()  # type: ignore
        self._queue.server.server_close()  # type: ignore

    def is_scanner_alive(self, scanner_id: str) -> bool:
        """Check is scanner alive.

        Args:
            scanner_id (str): hex id of scanner.

        Returns:
            bool: is scanner alive.
        """
        try:
            if self._config.scanners[scanner_id]["runtime"].process.is_alive():  # type: ignore
                return True
        except KeyError:
            pass
        return False

    def set_scanner_settings(
        self, scanner_id, settings: ScannerInternalSettings
    ) -> bool:
        # for scanner in self._scanners:
        #     if scanner.info.scanner_id == scanner_id:
        #         if scanner.process.is_alive():
        #             self._logger.info(
        #                 f"Applying new settings to scanner id #{scanner_id}..."
        #             )
        #         else:
        #             self._logger.warning(f"Scanner with id #{scanner_id} is not alive!")
        #             self._logger.warning(
        #                 f"Settings will be apllied after scanner resurrection!"
        #             )
        #         scanner.queue.put(settings)
        #         return True
        # self._config[scanner_id][]

        self._logger.error("No scanner with given ID found!")
        return False

    def _handle_handshake_message(self, handshake_message: HandshakeMessage):

        self._logger.debug("Got new connection!")
        self._logger.debug(f"\tClient IP:            {handshake_message.client_ip}")
        self._logger.debug(f"\tClient port:          {handshake_message.client_port}")

        scanner_id = self._is_client_registered(handshake_message.client_ip)
        if not scanner_id:
            self._logger.warning(
                f"Unregistred client connection from {handshake_message.client_ip}!"
            )
            handshake_message.client_socket.close()
            return

        runtime_settings = ScannerRuntimeSettings(
            port=handshake_message.client_port,
            queue=Queue(),
            process=Process(
                target=scanner_process, args=(self._config.scanners[scanner_id],)
            ),
            client_socket=handshake_message.client_socket,
        )

        self._config.scanners[scanner_id]["runtime"] = runtime_settings

        try:
            self._config.scanners[scanner_id]["runtime"].process.start()
        except AssertionError:
            name = self._config.scanners[scanner_id]["info"].name

            self._logger.warning(
                f"Process for scanner {name}: ID#{scanner_id} was already started and killed due to error."
            )
            self._logger.warning("Restarting process...")
            self._config.scanners[scanner_id]["runtime"].process = Process(
                target=scanner_process,
                args=(self._config.scanners[scanner_id],),
            )
            self._config.scanners[scanner_id]["runtime"].process.start()

    def _handle_client_message(self, client_message: ClientMessage):
        self._logger.debug("Got new message!")
        self._logger.debug(f"\tClient IP:            {client_message.client_ip}")
        self._logger.debug(f"\tClient port:          {client_message.client_port}")

        try:
            msg_scanner_id = get_scanner_id(client_message.client_message)
        except ProtocolMessageError as err:
            self._logger.error(str(err))
            return
        except Exception:
            self._logger.exception("Unhandled error:")
            self._logger.error(
                f"Raw message: {format_bytestring(client_message.client_message)}"
            )
            return

        # if not self._is_scanner_id_registered(msg_scanner_id):
        #     correct_id = 0
        #     for scanner in self._scanners:
        #         if client_message.client_ip == scanner.info.address:
        #             correct_id = scanner.info.scanner_id
        #             break
        #     self._logger.error(
        #         f"Client with address {client_message.client_ip} is registred, but has another ID: {correct_id}"
        #     )
        #     self._logger.error(
        #         f"Perhaps bad settings on {self._settings_path}, check it please."
        #     )
        #     self._logger.error(
        #         f"Skipped raw message: {format_bytestring(client_message.client_message)}"
        #     )
        #     return

        scanner = self._config.scanners[msg_scanner_id]

        if scanner["runtime"].process and scanner["runtime"].process.is_alive():
            scanner["runtime"].queue.put(client_message.client_message)
        else:
            try:
                scanner["runtime"].process.start()
            except AssertionError:
                name = scanner["info"].name
                self._logger.warning(
                    f"Process for scanner {name}: ID#{msg_scanner_id} was already started and killed due to error."
                )
                self._logger.warning("Restarting process...")
                scanner["runtime"].process = Process(
                    target=scanner_process,
                    args=(scanner,),
                )
                scanner["runtime"].process.start()

    def _emit_debug_scanner_info(
        self, scanner_id: str, scanner: ScannerSettings
    ) -> None:

        name = scanner["info"].name
        address = scanner["info"].address
        products = scanner["settings"].products
        server_ip = scanner["settings"].server_ip
        server_port = scanner["settings"].server_port
        gateway_ip = scanner["settings"].gateway_ip
        netmask = scanner["settings"].netmask

        self._logger.debug("Registered scanner:")
        self._logger.debug(f"\tScanner id:          {scanner_id}")
        self._logger.debug(f"\tScanner name:        {name}")
        self._logger.debug(f"\tScanner address:     {address}")
        self._logger.debug(f"\tScanner products:")
        for i in range(len(products)):
            self._logger.debug(f"\t\tProduct #{i}: {products[i]}")
        self._logger.debug(f"\tScanner server IP:   {server_ip}")
        self._logger.debug(f"\tScanner server port: {server_port}")
        self._logger.debug(f"\tScanner gateway IP:  {gateway_ip}")
        self._logger.debug(f"\tScanner netmask:     {netmask}")

    def register_single_scanner(
        self, scanner_id: str, scanner: ScannerSettings
    ) -> bool:
        """Performs registraion of a given scanner."""

        try:
            self._config.scanners[scanner_id]
        except KeyError:
            # ok
            self._config.scanners[scanner_id] = scanner
            self._logger.debug("Registered new scanner:")
            self._emit_debug_scanner_info(scanner_id, scanner)

            # save to settings
        else:
            self._logger.error(f"Scanner with ID {scanner_id} already registred!")
            return False

        return True

    def _is_client_registered(self, client_address: str) -> Optional[str]:
        for scanner in self._config.scanners:
            if self._config.scanners[scanner]["info"].address == client_address:
                return scanner
        return None

    def _is_scanner_id_registered(self, scanner_id: str) -> bool:
        try:
            self._config.scanners[scanner_id]
        except KeyError:
            return False
        return True
