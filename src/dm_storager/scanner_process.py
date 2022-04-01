import socket
import asyncio
import logging
import time

from multiprocessing import Process, Queue

from dm_storager.structs import ScannerInfo

from dm_storager.CSVWriter import CSVWriter

from dm_storager.utils.logger import configure_logger
from dm_storager.utils.packet_builer import build_packet
from dm_storager.utils.packet_parser import parse_input_message

from dm_storager.schema import (
    StateControlPacket,
    ScannerControlResponse,
    SettingsSetResponse,
    ArchieveDataResponce,
)

PING_PERIOD = 10
PING_TIMEOUT = 5


def scanner_process(scanner: ScannerInfo, queue: Queue):

    scanner_logger = configure_logger(f"Scanner #{scanner.scanner_id}", is_verbose=True)

    scanner_csv_writer = CSVWriter(scanner.scanner_id)

    packet_id: int = 0
    control_packet_id: int = 0

    is_alive: bool = True
    received_ping: bool = False

    scanner_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        scanner_socket.connect((scanner.address, scanner.port))
    except OSError:
        scanner_logger.error(f"Connection error: {scanner.address}:{scanner.port}")
        scanner_logger.error("Skipping scanner start.")
        return
    except Exception:
        scanner_logger.exception("Unhandled exception:")
        return

    async def wait_ping_response():
        nonlocal received_ping
        while received_ping is False:
            await asyncio.sleep(0.1)

    async def state_contol_logic():
        nonlocal packet_id
        nonlocal received_ping
        nonlocal is_alive

        scanner_logger.info(f"Sending ping packet #{packet_id} to scanner")
        control_packet = StateControlPacket(
            scanner_ID=scanner.scanner_id, packet_ID=packet_id
        )
        control_packet_id = packet_id

        bytes_packet = build_packet(control_packet)
        scanner_socket.send(bytes_packet)

        packet_id += 1
        packet_id %= 256

        try:
            await asyncio.wait_for(wait_ping_response(), timeout=PING_TIMEOUT)
        except asyncio.exceptions.TimeoutError:
            scanner_logger.error("STATE CONTROL PACKET TIMEOUT")
            is_alive = False
        else:
            scanner_logger.info("STATE CONTROL PACKET ACCEPTED")
            received_ping = False

        await asyncio.sleep(PING_PERIOD)

    def handle_state_control_response(packet: ScannerControlResponse):
        nonlocal is_alive
        nonlocal control_packet_id

        if packet.packet_id == control_packet_id:
            is_alive = True
        else:
            scanner_logger.error("Received packet id did not match to send packet id")
            is_alive = False

    def handle_settings_set_response(packet: SettingsSetResponse):

        if packet.response_code == 0:
            scanner_logger.info("Settings was succesfully applied!")
        else:
            scanner_logger.error(
                f"An error on scanner settings applying occurs: {packet.response_code}"
            )

    def handle_archieve_response(control_packet: ArchieveDataResponce):
        try:
            scanner_csv_writer.append_data(control_packet.archieve_data)
        except Exception:
            scanner_logger.exception("Storing to CSV Error:")

    async def scanner_message_hanler():

        if not queue.empty():
            message = queue.get()
            scanner_logger.info(f"Got message: {message}")
            parsed_packet = parse_input_message(message)

            if isinstance(parsed_packet, ScannerControlResponse):
                handle_state_control_response(parsed_packet)
            elif isinstance(parsed_packet, SettingsSetResponse):
                handle_settings_set_response(parsed_packet)
            elif isinstance(parsed_packet, ArchieveDataResponce):
                handle_archieve_response(parsed_packet)

    while is_alive:
        asyncio.run(state_contol_logic())
        asyncio.run(scanner_message_hanler())

        time.sleep(0.1)

    scanner_logger.error("State control packet was not received in time.")
    scanner_logger.error("Closing socket.")
    scanner_socket.close()

    scanner_logger.error(f"Closing process.")
