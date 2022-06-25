import time
import multiprocessing
from multiprocessing import Process, Queue
from typing import Tuple, Optional

from dm_storager import Config
from dm_storager.exceptions import BAD_HOST_ADDRESS, BAD_PORT, ServerStop

from dm_storager.protocol.packet_parser import PacketParser

from dm_storager.utils.config_manager import CONFIG_ENABLE_LIST, ConfigManager
from dm_storager.utils.logger import configure_logger

from dm_storager.scanner_process import scanner_process
from dm_storager.server_queue import ServerQueue
from dm_storager.structs import (
    ClientMessage,
    HandshakeMessage,
    ScannerInternalSettings,
    ScannerRuntimeSettings,
    ScannerSettings,
    ThreadList,
)


class Server:
    def __init__(self, config_manager: ConfigManager, debug: bool) -> None:
        self._is_debug = debug
        self._logger = configure_logger("ROOT_SERVER", debug)
        self._queue: Optional[ServerQueue] = None

        self._socket_thread_list: ThreadList = {}

        self._config_manager = config_manager
        self._config: Config = self._config_manager.config  # type: ignore

        self._parser = PacketParser(debug)
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

                self._process_monitor()

        except (KeyboardInterrupt, SystemExit):
            self.stop_server()
            raise ServerStop

    def stop_server(self) -> None:
        for scanner_id in self._config.scanners:
            self._stop_scanner_process(scanner_id)

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

    def update_scanner_settings(
        self, scanner_id, settings: Optional[ScannerInternalSettings] = None
    ) -> bool:
        try:
            if settings:
                self._config.scanners[scanner_id]["settings"] = settings
        except KeyError:
            self._logger.error("No scanner with given ID found!")
            return False

        if self.is_scanner_alive(scanner_id):
            current_setings: ScannerInternalSettings = self._config.scanners[
                scanner_id
            ][
                "settings"
            ]  # type: ignore

            self._config.scanners[scanner_id]["runtime"].queue.put(current_setings)  # type: ignore
            return True

        self._logger.warning(f"Scanner with id #{scanner_id} is not alive!")
        return False

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

    def _handle_handshake_message(self, handshake_message: HandshakeMessage):

        self._logger.debug("Got new connection!")
        self._logger.debug(
            f"\tClient address:            {handshake_message.client_ip}:{handshake_message.client_port}"
        )

        # Validate new client. If not registred: drops it.
        scanner_id = self._is_client_registered(handshake_message.client_ip)
        if not scanner_id:
            self._logger.warning(
                f"Unregistred client connection from {handshake_message.client_ip}!"
            )
            handshake_message.client_socket.close()
            return

        # Create runtime info dict
        runtime_settings = ScannerRuntimeSettings(
            port=handshake_message.client_port,
            queue=Queue(),
            process=Process(
                target=scanner_process,
                args=(scanner_id, self._config.scanners[scanner_id], self._is_debug),
            ),
            client_socket=handshake_message.client_socket,
        )
        self._config.scanners[scanner_id]["runtime"] = runtime_settings

        # Add pair socket-thread.
        # Thread are non-copyable objects, so it's impossible put them in runtime dict
        self._socket_thread_list.update(
            {scanner_id: handshake_message.client_socket_thread}
        )

        # Start scanner process
        try:
            self._config.scanners[scanner_id]["runtime"].process.start()  # type: ignore
        except AssertionError:
            name = self._config.scanners[scanner_id]["info"].name  # type: ignore

            self._logger.warning(
                f"Process for scanner {name}: ID# {scanner_id} was already started and killed due to error."
            )
            self._logger.warning("Restarting process...")
            self._config.scanners[scanner_id]["runtime"].process = Process(
                target=scanner_process,
                args=(
                    scanner_id,
                    self._config.scanners[scanner_id],
                ),
            )
            self._config.scanners[scanner_id]["runtime"].process.start()  # type: ignore

        # Send settings to scanner after handshake
        update_scanner_settings: bool = (
            self._config.scanners[scanner_id]["info"].update_settings_on_connect  # type: ignore
            in CONFIG_ENABLE_LIST
        )
        if update_scanner_settings:
            self.update_scanner_settings(scanner_id)

    def _handle_client_message(self, client_message: ClientMessage):
        self._logger.debug("Got new message!")
        self._logger.debug(
            f"\tClient address:            {client_message.client_ip}:{client_message.client_port}"
        )

        msg_scanner_id = self._parser.extract_scanner_id(client_message.client_message)
        if msg_scanner_id is None:
            return

        # Verify match scanner ID and client IPs
        if not self._is_scanner_id_registered(msg_scanner_id):
            correct_id = self._is_client_registered(client_message.client_ip)

            self._logger.error(
                f"Client with address {client_message.client_ip} is registred, but has another ID: {correct_id}"
            )
            self._logger.error(
                f"Perhaps bad settings on {self._config_manager.config_path}, check it please."
            )
            self._logger.error("Skipped this message.")
            return

        scanner = self._config.scanners[msg_scanner_id]

        if self.is_scanner_alive(msg_scanner_id):
            scanner["runtime"].queue.put(client_message.client_message)  # type: ignore
        else:
            try:
                scanner["runtime"].process.start()  # type: ignore
            except KeyError:
                pass
            except AssertionError:
                name = scanner["info"].name  # type: ignore
                self._logger.warning(
                    f"Process for scanner {name}: ID#{msg_scanner_id} was already started and killed due to error."
                )
                self._logger.warning("Restarting process...")

                self._config.scanners[msg_scanner_id]["runtime"].process = Process(
                    target=scanner_process,
                    args=(
                        msg_scanner_id,
                        self._config.scanners[msg_scanner_id],
                    ),
                )
                self._config.scanners[msg_scanner_id]["runtime"].process.start()  # type: ignore

    def _emit_debug_scanner_info(
        self, scanner_id: str, scanner: ScannerSettings
    ) -> None:
        """Emits all scanner info in debug mode.

        Args:
            scanner_id (str): ID of scanner in HEX mode.
            scanner (ScannerSettings): Dict with scanner info and internal settings.
        """

        name = scanner["info"].name  # type: ignore
        address = scanner["info"].address  # type: ignore
        products = scanner["settings"].products  # type: ignore
        server_ip = scanner["settings"].server_ip  # type: ignore
        server_port = scanner["settings"].server_port  # type: ignore
        gateway_ip = scanner["settings"].gateway_ip  # type: ignore
        netmask = scanner["settings"].netmask  # type: ignore

        self._logger.debug("Registered scanner:")
        self._logger.debug(f"\tScanner id:          {scanner_id}")
        self._logger.debug(f"\tScanner name:        {name}")
        self._logger.debug(f"\tScanner address:     {address}")
        self._logger.debug("\tScanner products:")
        for i in range(len(products)):
            self._logger.debug(f"\t\tProduct #{i}: {products[i]}")
        self._logger.debug(f"\tScanner server IP:   {server_ip}")
        self._logger.debug(f"\tScanner server port: {server_port}")
        self._logger.debug(f"\tScanner gateway IP:  {gateway_ip}")
        self._logger.debug(f"\tScanner netmask:     {netmask}")

    def _is_client_registered(self, client_address: str) -> Optional[str]:
        """Checks if address of client is presented in config.

        Checks all registered scanners' addressed one by one.

        Args:
            client_address (str): IPv4 address of client.

        Returns:
            Optional[bool]: scanner ID if registred, else None
        """
        for scanner in self._config.scanners:
            if self._config.scanners[scanner]["info"].address == client_address:  # type: ignore
                return scanner
        return None

    def _is_scanner_id_registered(self, scanner_id: str) -> bool:
        """Checks if scanner is presented in config.

        Validation is made by key - scanner_id.

        Args:
            scanner_id (str): key in config dict.

        Returns:
            bool: is scanner registered.
        """
        try:
            self._config.scanners[scanner_id]
        except KeyError:
            return False
        return True

    def _process_monitor(self):
        """
        Health monitor for scanner processes.
        If scanner stops due to ping timeout or runtime error - closes socket.
        If socket is closed by client or runtime error - closes scanner process.

        Scanner might not have RUNTIME data, so it is not started. It is ok.
        """
        for scanner in self._config.scanners:
            try:
                _p: Process = self._config.scanners[scanner]["runtime"].process  # type: ignore

                if not _p.is_alive():
                    self._stop_scanner_socket(scanner)
                    continue

                # process is alive, but socket might be closed by scanner
                if (
                    getattr(self._socket_thread_list[scanner], "enabled_socket")
                    is False
                ):
                    self._logger.warning(
                        f"Scanner #{scanner} closed socket.",
                    )
                    self._stop_scanner_process(scanner)

            except KeyError:
                pass

    def _stop_scanner_socket(self, scanner_id: str) -> None:
        _t = self._socket_thread_list[scanner_id]
        setattr(_t, "enabled_socket", False)

    def _stop_scanner_process(self, scanner_id: str) -> None:
        try:
            if (
                self._config.scanners[scanner_id]["runtime"].process  # type: ignore
                and self._config.scanners[scanner_id]["runtime"].process.pid  # type: ignore
            ):
                self._logger.warning(
                    f"Scanner #{scanner_id}: killing process.",
                )
                self._config.scanners[scanner_id]["runtime"].process.kill()  # type: ignore
        except KeyError:
            pass
