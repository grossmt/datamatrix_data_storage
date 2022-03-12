import socket
import asyncio
import logging
import time

from multiprocessing import Process, Queue

from dm_storager.structs import ScannerInfo, StateControlPacket
from dm_storager.utils.packet_builer import build_packet
from dm_storager.utils.packet_parser import parse_input_message

from dm_storager.schema import (
    ScannerControlResponse,
    SettingsSetResponse,
    ArchieveDataResponce,
)

PING_PERIOD = 10
PING_TIMEOUT = 2


def scanner_process(scanner: ScannerInfo, queue: Queue):

    SCANNER_LOGGER = logging.getLogger(f"Scanner #{scanner.scanner_id}")
    SCANNER_LOGGER.setLevel(logging.INFO)

    packet_id: int = 0
    control_packet_id: int = 0

    is_alive: bool = True
    received_ping: bool = False

    scanner_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    scanner_socket.connect((scanner.address, scanner.port))

    async def wait_ping_response():
        nonlocal received_ping
        while received_ping is False:
            await asyncio.sleep(0.1)

    async def state_contol_logic():
        nonlocal packet_id
        nonlocal received_ping
        nonlocal is_alive

        SCANNER_LOGGER.info(f"Sending ping packet #{packet_id} to scanner")
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
            SCANNER_LOGGER.error("STATE CONTROL PACKET TIMEOUT")
            is_alive = False
        else:
            SCANNER_LOGGER.info("STATE CONTROL PACKET ACCEPTED")
            received_ping = False

        await asyncio.sleep(PING_PERIOD)

    def handle_state_control_response(packet: ScannerControlResponse):
        nonlocal is_alive
        nonlocal control_packet_id

        if packet.packet_id == control_packet_id:
            is_alive = True
        else:
            SCANNER_LOGGER.error("Received packet id did not match to send packet id")
            is_alive = False

    def handle_settings_set_response(packet: SettingsSetResponse):

        if packet.response_code == 0:
            SCANNER_LOGGER.info("Settings was succesfully applied!")
        else:
            SCANNER_LOGGER.error(
                f"An error on scanner settings applying occurs: {packet.response_code}"
            )

    def handle_archieve_response(control_packet: ArchieveDataResponce):
        pass

    async def scanner_message_hanler():

        if not queue.empty():
            message = queue.get()
            SCANNER_LOGGER.info(f"Got message: {message}")
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

    SCANNER_LOGGER.error("State control packet was not received in time.")
    SCANNER_LOGGER.error("Closing socket.")
    scanner_socket.close()

    SCANNER_LOGGER.error(f"Closing process.")
