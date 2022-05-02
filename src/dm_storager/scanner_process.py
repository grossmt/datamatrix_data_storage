import socket
import asyncio
import time
import sys

from multiprocessing import Queue

from dm_storager.protocol.const import (
    PACKET_ID_LEN,
    PREAMBULA,
    PacketCode,
    ResponseCode,
)
from dm_storager.protocol.exceptions import ProtocolMessageError
from dm_storager.protocol.utils import format_bytestring

from dm_storager.structs import Scanner, ScannerInfo, ScannerSettings
from dm_storager.CSVWriter import CSVWriter
from dm_storager.enviroment import HOST_IP, HOST_PORT
from dm_storager.utils.logger import configure_logger
from dm_storager.protocol.packet_builer import build_packet
from dm_storager.protocol.packet_parser import get_packet_code, parse_input_message
from dm_storager.protocol.schema import (
    ArchieveDataRequest,
    SettingsSetRequest,
    StateControlRequest,
    ScannerControlResponse,
    SettingsSetResponse,
    ArchieveDataResponse,
)


# def scanner_process(scanner: ScannerInfo, queue: Queue):
def scanner_process(scanner: Scanner):
    class ScannerHandler:

        PING_PERIOD = 10
        PING_TIMEOUT = 500
        PRODUCT_LIST_SIZE = 6

        def __init__(self, scanner: Scanner) -> None:

            self._queue: Queue = scanner.queue
            self._scanner_csv_writer = CSVWriter(scanner.info.scanner_id)
            self._logger = configure_logger(
                f"Scanner #{scanner.info.scanner_id}", is_debug=True
            )

            self._info = scanner.info
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
                netmask="",
            )

            self._socket = scanner.client_socket

            # try:
            #     self._socket.connect((scanner.address, scanner.port))
            # except TimeoutError:
            #     self._logger.exception(
            #         f"Connection timeout to: {scanner.address}:{scanner.port}"
            #     )
            #     self._logger.error("Skipping scanner start.")
            #     self._is_alive = False
            # except OSError:
            #     self._logger.exception(
            #         f"Connection error: {scanner.address}:{scanner.port}"
            #     )
            #     self._logger.error("Skipping scanner start.")
            #     self._is_alive = False
            # except Exception:
            #     self._logger.exception("Unhandled exception:")
            #     self._logger.error("Skipping scanner start.")
            #     self._is_alive = False

        @property
        def is_alive(self) -> bool:
            return self._is_alive

        def _handle_state_control_response(self, message: bytes):
            self._received_ping = True

            try:
                parsed_packet = parse_input_message(message)
            except ProtocolMessageError as ex:
                self._logger.exception(ex)
                return
            except Exception as ex:
                self._logger.exception(ex)
                return

            if parsed_packet.packet_ID == self._control_packet_id:  # type: ignore
                self._control_packet_id += 1
                self._control_packet_id %= 2 ** (PACKET_ID_LEN * 2)
                self._is_alive = True
            else:
                self._logger.error("Received packet id did not match to send packet id")

        def _handle_settings_set_response(self, message: bytes):

            self._received_ping = True

            try:
                parsed_packet = parse_input_message(message)
            except ProtocolMessageError as ex:
                self._logger.exception(ex)
                return
            except Exception as ex:
                self._logger.exception(ex)
                return

            if parsed_packet.packet_ID != self._settings_packet_id:  # type: ignore
                self._logger.error(
                    f"Response packet id does not match to sent packet id!"
                )
                self._logger.error(f"\tSent packet id: {self._settings_packet_id}")
                self._logger.error(f"\tReceived packet id: {parsed_packet.packet_ID}")  # type: ignore
                return

            self._settings_packet_id += 1
            self._settings_packet_id %= 2 ** (PACKET_ID_LEN * 2)

            if parsed_packet.response_code == ResponseCode.SUCCSESS:  # type: ignore
                self._logger.info("Settings were succesfully applied!")

                self._logger.debug("New scanner settings:")
                for i in range(ScannerHandler.PRODUCT_LIST_SIZE):
                    self._logger.debug(
                        f"\tProduct #{i}: {self._scanner_settings.products[i]}"
                    )

                self._logger.debug(
                    f"\tServer IP:    {self._scanner_settings.server_ip}"
                )
                self._logger.debug(
                    f"\tServer Port:  {self._scanner_settings.server_port}"
                )
                self._logger.debug(
                    f"\tGateway IP:   {self._scanner_settings.server_ip}"
                )
                self._logger.debug(
                    f"\tNetmask:      {self._scanner_settings.server_ip}"
                )
            else:
                self._logger.error(
                    f"An error on scanner settings applying occurs: {parsed_packet.response_code}"  # type: ignore
                )

        def _handle_archieve_request(self, message: bytes):

            self._received_ping = True

            response_packet = ArchieveDataResponse(
                PREAMBULA,
                self._info.scanner_id,
                self._archieve_data_packet_id,
                packet_code=PacketCode.ARCHIEVE_DATA_CODE,
                response_code=ResponseCode.ERROR,
            )

            try:
                parsed_packet = parse_input_message(message)
            except ProtocolMessageError as ex:
                self._logger.exception(ex)
                b_response_packet = build_packet(response_packet)
                self._socket.send(b_response_packet)
                return
            except Exception as ex:
                self._logger.exception(ex)
                return
            finally:
                self._archieve_data_packet_id += 1
                self._archieve_data_packet_id %= 2 ** (PACKET_ID_LEN * 2)

            try:
                self._scanner_csv_writer.append_data(parsed_packet.archieve_data, self._scanner_settings)  # type: ignore
            except Exception:
                self._logger.exception("Storing to CSV Error:")
                b_response_packet = build_packet(response_packet)
                self._socket.send(b_response_packet)
                return

            response_packet.response_code = ResponseCode.SUCCSESS
            b_response_packet = build_packet(response_packet)
            self._socket.send(b_response_packet)

        def _apply_new_scanner_settings(self, new_settings: ScannerSettings) -> None:

            for i in range(ScannerHandler.PRODUCT_LIST_SIZE):
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
                preambula=PREAMBULA,
                scanner_ID=self._info.scanner_id,
                packet_ID=self._settings_packet_id,
                packet_code=PacketCode.SETTINGS_SET_CODE,
                settings=self._scanner_settings,  # type: ignore
            )

            bytes_packet = build_packet(settings_packet)
            try:
                self._socket.send(bytes_packet)
            except Exception as ex:
                self._logger.error("New settings were not applided to scanner. Reason:")
                self._logger.exception(ex)
            else:
                self._logger.debug("Waiting for response from scanner...")

        async def _wait_ping_response(self):
            while self._received_ping is False:
                await asyncio.sleep(0.1)

        async def _state_contol_logic(self):
            print("ololo")
            self._logger.debug(
                f"Sending ping packet #{self._control_packet_id} to scanner"
            )
            control_packet = StateControlRequest(
                PREAMBULA,
                self._info.scanner_id,
                self._control_packet_id,
                PacketCode.STATE_CONTROL_CODE,
                reserved=0,
            )

            bytes_packet = build_packet(control_packet)
            try:
                self._socket.send(bytes_packet)
            except Exception as ex:
                self._logger.exception(ex)
                self._is_alive = False
                return

            try:
                asyncio.wait_for(
                    self._wait_ping_response(), timeout=ScannerHandler.PING_TIMEOUT
                )
            except asyncio.exceptions.TimeoutError:
                self._logger.error("State control packet timeout!")
                self._is_alive = False
            else:
                self._logger.info("STATE CONTROL PACKET ACCEPTED")
                self._received_ping = False

            await asyncio.sleep(ScannerHandler.PING_PERIOD)

        async def _scanner_message_hanler(self):
            if not self._queue.empty():
                print("lolol")

                message = self._queue.get()

                if isinstance(message, ScannerSettings):
                    self._apply_new_scanner_settings(message)

                elif isinstance(message, bytes):
                    self._logger.debug(f"Got message: {format_bytestring(message)}")

                    try:
                        packet_code = get_packet_code(message)
                    except Exception as ex:
                        self._logger.exception(ex)
                        return

                    if packet_code == PacketCode.STATE_CONTROL_CODE:
                        self._handle_state_control_response(message)
                    elif packet_code == PacketCode.SETTINGS_SET_CODE:
                        self._handle_settings_set_response(message)
                    elif packet_code == PacketCode.ARCHIEVE_DATA_CODE:
                        self._handle_archieve_request(message)
                    else:
                        self._logger.error(f"")

        def run_process(self):
            self._logger.debug(f"Start of process of {scanner.info.name}")

            while self._is_alive:
                # asyncio.run(self._state_contol_logic())
                asyncio.run(self._scanner_message_hanler())

                # time.sleep(0.1)
                # asyncio.run(time.sleep(0.1))

            self._logger.error("State control packet was not received in time.")
            self._logger.error("Closing socket.")
            self._socket.close()
            self._logger.error(f"Closing process.")

    scanner_handler = ScannerHandler(scanner)

    if scanner_handler.is_alive:
        scanner_handler.run_process()
    else:
        scanner_handler._logger.error(
            "Failed to initialize scanner handler in process."
        )
        scanner_handler._logger.error(f"Closing process.")

    sys.exit()
