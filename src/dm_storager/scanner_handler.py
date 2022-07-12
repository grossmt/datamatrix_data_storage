import asyncio
from pathlib import Path
from socket import socket
from multiprocessing import Queue
from datetime import datetime

from dm_storager.protocol.const import (
    ProtocolDesc,
    HeaderDesc,
    PacketCode,
    ResponseCode,
)
from dm_storager.structs import (
    FileFormat,
    Scanner,
    ScannerInternalSettings,
)
from dm_storager.file_writer import FileWriter
from dm_storager.utils.logger import configure_logger
from dm_storager.protocol.packet_builer import PacketBuilder
from dm_storager.protocol.packet_parser import PacketParser


from dm_storager.protocol.schema import (
    StateControlRequest,
    SettingsSetRequest,
    ArchieveDataResponse,
    ScannerControlResponse,
    SettingsSetResponse,
    ArchieveDataRequest,
)


class ScannerHandler:

    PING_PERIOD = 30
    PING_TIMEOUT = 10
    PRODUCT_LIST_SIZE = 6

    def __init__(
        self,
        scanner: Scanner,
        data_path: Path,
        is_debug: bool = False,
    ) -> None:

        # Extract objects from scanner class
        self._scanner_id = scanner.scanner_id
        self._scanner_name = scanner.info.name

        self._info = scanner.info
        self._scanner_settings: ScannerInternalSettings = scanner.settings
        self._queue: Queue = scanner.runtime.queue  # type: ignore
        self._socket: socket = scanner.runtime.client_socket  # type: ignore
        self._port = scanner.runtime.port

        # Local objects
        self._scanner_file_writer = FileWriter(
            self._scanner_name, self._scanner_id, FileFormat.TXT, data_folder=data_path
        )
        self._logger = configure_logger(f"SCAN {self._scanner_id}", is_debug)
        self._packet_builder = PacketBuilder(is_debug)
        self._packet_parser = PacketParser(is_debug)

        # Runtime vars
        self._current_packet_id: int = 0
        self._is_alive: bool = True
        self._received_ping: bool = False
        self._last_packet_timestamp = datetime.now()

        self._loop = asyncio.get_event_loop()

    @property
    def is_alive(self) -> bool:
        return self._is_alive

    def run_process(self):
        """Runs scanner process in loop.
        Loop runs while scanner is alive.
        """
        self._logger.info(f"Start of process of {self._info.name}")

        self._loop.run_until_complete(
            asyncio.gather(
                self._state_contol_logic(),
                self._scanner_message_hanler(),
            )
        )

        self._stop_process()

    def _stop_process(self):
        """Send close message to server."""
        self._loop.close()

        self._logger.error("Closing process.")

    async def _state_contol_logic(self):

        while self.is_alive:
            await asyncio.sleep(ScannerHandler.PING_PERIOD / 2)

            now = datetime.now()
            delta = now - self._last_packet_timestamp

            if delta.total_seconds() < ScannerHandler.PING_PERIOD:
                continue

            self._logger.debug(
                f"Sending ping packet #{self._current_packet_id} to scanner"
            )
            control_packet = StateControlRequest(
                ProtocolDesc.PREAMBULA,
                self._scanner_id,
                self._current_packet_id,
                PacketCode.STATE_CONTROL_CODE,
                reserved=0,
            )

            bytes_packet = self._packet_builder.build_packet(control_packet)

            try:
                self._socket.send(bytes_packet)
            except Exception as ex:
                self._logger.exception(ex)
                self._is_alive = False
                return

            try:
                await asyncio.wait_for(
                    self._wait_ping_response(), timeout=ScannerHandler.PING_TIMEOUT
                )
                await asyncio.sleep(0.1)
            except asyncio.exceptions.TimeoutError:
                self._logger.error("State control packet timeout!")
                self._is_alive = False
            else:
                self._received_ping = False

    async def _wait_ping_response(self):
        while self._received_ping is False:
            await asyncio.sleep(0.1)
        return

    async def _scanner_message_hanler(self):

        while self._is_alive:

            if not self._queue.empty():
                message = self._queue.get()

                if isinstance(message, ScannerInternalSettings):
                    self._apply_new_scanner_settings(message)
                    continue

                packet_code = self._packet_parser.extract_packet_code(message)

                if packet_code == PacketCode.STATE_CONTROL_CODE:
                    self._handle_state_control_response(message)
                elif packet_code == PacketCode.SETTINGS_SET_CODE:
                    self._handle_settings_set_response(message)
                elif packet_code == PacketCode.ARCHIEVE_DATA_CODE:
                    self._handle_archieve_request(message)
                else:
                    self._logger.error("Got unexpected Packet code.")
                    skipped_message = self._packet_parser.format_byte_string(
                        "Skipped message", message
                    )
                    self._logger.error(skipped_message)

            await asyncio.sleep(0.5)

    def _handle_state_control_response(self, message: bytes):
        self._received_ping = True
        self._last_packet_timestamp = datetime.now()

        packet = self._packet_parser.parse_message(message)
        if not isinstance(packet, ScannerControlResponse):
            return

        if packet.packet_ID == self._current_packet_id:
            self._current_packet_id += 1
            self._current_packet_id %= 2 ** (HeaderDesc.PACKET_ID_LEN * 2)
            self._is_alive = True
            self._logger.info("State control packet accepted")
        else:
            self._logger.warning("Received packet id did not match to send packet id")

    def _handle_settings_set_response(self, message: bytes):

        self._received_ping = True
        self._last_packet_timestamp = datetime.now()

        packet = self._packet_parser.parse_message(message)
        if not isinstance(packet, SettingsSetResponse):
            return

        if packet.packet_ID != self._current_packet_id:
            self._logger.warning("Response packet id does not match to sent packet id!")
            self._logger.warning(f"\tSent packet id: {self._current_packet_id}")
            self._logger.warning(f"\tReceived packet id: {packet.packet_ID}")
            return

        self._current_packet_id += 1
        self._current_packet_id %= 2 ** (HeaderDesc.PACKET_ID_LEN * 2)

        if packet.response_code == ResponseCode.SUCCSESS:
            self._logger.info("Settings were succesfully applied!")

            self._logger.debug("New scanner settings:")
            for i in range(ScannerHandler.PRODUCT_LIST_SIZE):
                self._logger.debug(
                    f"\tProduct #{i}: {self._scanner_settings.products[i]}"
                )

            self._logger.debug(f"\tServer IP:    {self._scanner_settings.server_ip}")
            self._logger.debug(f"\tServer Port:  {self._scanner_settings.server_port}")
            self._logger.debug(f"\tGateway IP:   {self._scanner_settings.server_ip}")
            self._logger.debug(f"\tNetmask:      {self._scanner_settings.server_ip}")
        else:
            self._logger.error(
                f"An error on scanner settings applying occurs: {packet.response_code}"
            )

    def _handle_archieve_request(self, message: bytes):
        self._received_ping = True
        self._last_packet_timestamp = datetime.now()

        response_packet = ArchieveDataResponse(
            ProtocolDesc.PREAMBULA,
            self._scanner_id,
            self._current_packet_id,
            packet_code=PacketCode.ARCHIEVE_DATA_CODE,
            response_code=ResponseCode.ERROR,
        )

        packet = self._packet_parser.parse_message(message)
        if not isinstance(packet, ArchieveDataRequest):
            self._logger.error("Archieve data is not accepted. Sending error ticket.")
            b_response_packet = self._packet_builder.build_packet(response_packet)
            self._socket.send(b_response_packet)
            return

        try:
            self._scanner_file_writer.append_data(
                packet.archieve_data, self._scanner_settings
            )
        except Exception as ex:
            self._logger.error("Storing data to File Error:")
            self._logger.error(ex)
            b_response_packet = self._packet_builder.build_packet(response_packet)
            self._socket.send(b_response_packet)
            return

        self._logger.info("Archieve data is accepted. Sending success ticket.")
        response_packet.response_code = ResponseCode.SUCCSESS
        b_response_packet = self._packet_builder.build_packet(response_packet)
        self._socket.send(b_response_packet)

        self._current_packet_id += 1
        self._current_packet_id %= 2 ** (HeaderDesc.PACKET_ID_LEN * 2)

    def _apply_new_scanner_settings(
        self, new_settings: ScannerInternalSettings
    ) -> None:

        for i in range(len(self._scanner_settings.products)):
            self._scanner_settings.products[i] = (
                new_settings.products[i] or self._scanner_settings.products[i]
            )

        self._scanner_settings.server_ip = (
            new_settings.server_ip or self._scanner_settings.server_ip
        )
        self._scanner_settings.server_port = (
            new_settings.server_port or self._scanner_settings.server_port
        )
        self._scanner_settings.gateway_ip = (
            new_settings.gateway_ip or self._scanner_settings.gateway_ip
        )
        self._scanner_settings.netmask = (
            new_settings.netmask or self._scanner_settings.netmask
        )

        self._logger.info("Sending new settings to scannner...")

        settings_packet = SettingsSetRequest(
            preambula=ProtocolDesc.PREAMBULA,
            scanner_ID=self._scanner_id,
            packet_ID=self._current_packet_id,
            packet_code=PacketCode.SETTINGS_SET_CODE,
            settings=self._scanner_settings,  # type: ignore
            reserved=0,
        )

        bytes_packet = self._packet_builder.build_packet(settings_packet)
        try:
            self._socket.send(bytes_packet)
        except Exception as ex:
            self._logger.error("New settings were not applided to scanner. Reason:")
            self._logger.error(ex)
        else:
            self._logger.debug("Waiting for response from scanner...")
