import socket
import asyncio
import time
import sys

from multiprocessing import Queue

from dm_storager.structs import ScannerInfo, ScannerSettings
from dm_storager.CSVWriter import CSVWriter
from dm_storager.enviroment import HOST_IP, HOST_PORT
from dm_storager.utils.logger import configure_logger
from dm_storager.protocol.packet_builer import build_packet
from dm_storager.protocol.packet_parser import parse_input_message
from dm_storager.schema import (
    StateControlPacket,
    ScannerControlResponse,
    SettingsSetResponse,
    ArchieveDataResponce,
)


def scanner_process(scanner: ScannerInfo, queue: Queue):
    class ScannerHandler:

        PING_PERIOD = 10
        PING_TIMEOUT = 5
        PRODUCT_LIST_SIZE = 6

        def __init__(self, scanner: ScannerInfo, queue: Queue) -> None:
            self._queue: Queue = queue
            self._scanner_csv_writer = CSVWriter(scanner.scanner_id)
            self._logger = configure_logger(
                f"Scanner #{scanner.scanner_id}", is_debug=True
            )

            self._control_packet_id: int = 0
            self._settings_packet_id: int = 0
            self._archieve_data_packet_id: int = 0

            self._is_alive: bool = True
            self._received_ping: bool = False

            self._scanner_settings = ScannerSettings(
                products=list("" for i in range(ScannerHandler.PRODUCT_LIST_SIZE)),
                server_ip=HOST_IP,
                server_port=HOST_PORT,
                gateway_ip="",
                netmask=""
            )

            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self._socket.connect((scanner.address, scanner.port))
            except TimeoutError:
                self._logger.exception(
                    f"Connection timeout to: {scanner.address}:{scanner.port}"
                )
                self._logger.error("Skipping scanner start.")
                self._is_alive = False
            except OSError:
                self._logger.exception(
                    f"Connection error: {scanner.address}:{scanner.port}"
                )
                self._logger.error("Skipping scanner start.")
                self._is_alive = False
            except Exception:
                self._logger.exception("Unhandled exception:")
                self._logger.error("Skipping scanner start.")
                self._is_alive = False

        @property
        def is_alive(self) -> bool:
            return self._is_alive

        def _handle_state_control_response(self, packet: ScannerControlResponse):
            if packet.packet_id == self._control_packet_id:
                self._is_alive = True
            else:
                self._logger.error("Received packet id did not match to send packet id")
                self._is_alive = False

        def _handle_settings_set_response(self, packet: SettingsSetResponse):
            if packet.response_code == 0:
                self._logger.info("Settings was succesfully applied!")
            else:
                self._logger.error(
                    f"An error on scanner settings applying occurs: {packet.response_code}"
                )

        def _handle_archieve_response(self, control_packet: ArchieveDataResponce):
            try:
                self._scanner_csv_writer.append_data(control_packet.archieve_data)
            except Exception:
                self._logger.exception("Storing to CSV Error:")

        def _apply_new_scanner_settings(self, new_settings: ScannerSettings) -> None:
            
            for i in range(ScannerHandler.PRODUCT_LIST_SIZE):
                self._scanner_settings.products[i] = new_settings.products[i] or self._scanner_settings.products[i]
            
            self._scanner_settings.server_ip = new_settings.server_ip or self._scanner_settings.server_ip
            self._scanner_settings.server_port = new_settings.server_port or self._scanner_settings.server_port
            self._scanner_settings.gateway_ip = new_settings.gateway_ip or self._scanner_settings.gateway_ip
            self._scanner_settings.netmask = self._scanner_settings.netmask if new_settings.netmask == "" else new_settings.netmask

            self._logger.info(f"Applied new settings to scanner #")

        async def _wait_ping_response(self):
            while self._received_ping is False:
                await asyncio.sleep(0.1)

        async def _state_contol_logic(self):

            self._logger.info(f"Sending ping packet #{self._packet_id} to scanner")
            control_packet = StateControlPacket(
                scanner_ID=scanner.scanner_id, packet_ID=self._packet_id
            )
            self._control_packet_id = self._packet_id

            bytes_packet = build_packet(control_packet)
            self._socket.send(bytes_packet)

            self._packet_id += 1
            self._packet_id %= 256

            try:
                await asyncio.wait_for(self._wait_ping_response(), timeout=ScannerHandler.PING_TIMEOUT)
            except asyncio.exceptions.TimeoutError:
                self._logger.error("STATE CONTROL PACKET TIMEOUT")
                self._is_alive = False
            else:
                self._logger.info("STATE CONTROL PACKET ACCEPTED")
                self._received_ping = False

            await asyncio.sleep(ScannerHandler.PING_PERIOD)

        async def _scanner_message_hanler(self):

            if not self._queue.empty():
                message = self._queue.get()

                if isinstance(message, ScannerSettings):
                    pass
                elif isinstance(message, bytes):
                    self._logger.debug(f"Got message: {message}")
                    parsed_packet = parse_input_message(message)

                    if isinstance(parsed_packet, ScannerControlResponse):
                        self._handle_state_control_response(parsed_packet)
                    elif isinstance(parsed_packet, SettingsSetResponse):
                        self._handle_settings_set_response(parsed_packet)
                    elif isinstance(parsed_packet, ArchieveDataResponce):
                        self._handle_archieve_response(parsed_packet)

        def run_process(self):
            self._logger.debug(f"Start of process of {scanner.name}")

            while self._is_alive:
                asyncio.run(self._state_contol_logic())
                asyncio.run(self._scanner_message_hanler())

                time.sleep(0.1)

            self._logger.error("State control packet was not received in time.")
            self._logger.error("Closing socket.")
            self._socket.close()

            self._logger.error(f"Closing process.")

    scanner_handler = ScannerHandler(scanner, queue)

    if scanner_handler.is_alive:
        scanner_handler.run_process()
    else:
        scanner_handler._logger.error(
            "Failed to initialize scanner handler in process."
        )
        scanner_handler._logger.error(f"Closing process.")

    sys.exit()
