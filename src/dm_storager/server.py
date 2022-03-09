from asyncio import futures
from dataclasses import dataclass
import socket
import time
import logging
import json
import multiprocessing, asyncio
import os
import datetime

from async_timeout import timeout, timeout_at
from multiprocessing import Process, Queue
from typing import Tuple, List, Optional, Union, Any
from pathlib import Path
from json import JSONDecodeError


# from dm_storager.json_parser import
from dm_storager.server_queue import ServerQueue
from dm_storager.structs import (
    ClientMessage,
    ScannerHandler,
    ScannerInfo,
    StateControlPacket,
    SettingsSetRequestPacket,
)

from dm_storager.const import SCANNER_SETTINGS

LOGGER = logging.getLogger("Server")
LOGGER.setLevel(logging.INFO)


def resolve_scanners_settings(
    settings_path: Path = SCANNER_SETTINGS,
) -> Optional[List[ScannerInfo]]:
    LOGGER.info(f"Resolving settings of scanners from {str(settings_path)}")

    scanners: List[ScannerInfo] = []
    try:
        with open(settings_path, "r") as settings_file:
            scanners_json_settings = json.load(settings_file)
    except FileNotFoundError:
        LOGGER.error(f"{str(settings_path)} file not found!")
        return None
    except JSONDecodeError as j_error:
        LOGGER.error("An exception during json reading occurs:")
        LOGGER.error(str(j_error))
        return None
    except Exception as ex:
        LOGGER.error("An unhandled error during json reading occurs:")
        print(str(ex))
        return None

    for record in scanners_json_settings["scanners"]:
        new_scanner = ScannerInfo(
            address=record["address"],
            port=record["port"],
            scanner_id=record["id"],
        )
        scanners.append(new_scanner)

    return scanners


def build(packet: Union[StateControlPacket, SettingsSetRequestPacket]) -> bytes:

    bytes_pack = bytearray()

    if isinstance(packet, StateControlPacket):
        b_preambula = bytes(packet.preambula, "cp1251")
        b_scanner_id = packet.scanner_ID.to_bytes(
            packet.scanner_ID_len, byteorder="big"
        )
        b_packet_id = packet.packet_ID.to_bytes(packet.packet_ID_len, byteorder="big")
        b_packet_code = packet.packet_code.to_bytes(
            packet.packet_code_len, byteorder="big"
        )
        b_reserved = packet.reserved.to_bytes(packet.reserved_len, byteorder="big")

        bytes_pack.extend(b_preambula)
        bytes_pack.extend(b_scanner_id)
        bytes_pack.extend(b_packet_id)
        bytes_pack.extend(b_packet_code)
        bytes_pack.extend(b_reserved)

        bytes_pack.extend(b"\x13")
        # assert_equivalent(len(bytes_pack), packet.packet_size)
    elif isinstance(packet, SettingsSetRequestPacket):
        pass
    else:
        raise

    return bytes_pack


PING_PERIOD = 4
PING_TIMEOUT = 2


def scanner_process(scanner: ScannerInfo, queue: Queue):

    packet_id = 0

    is_alive = True
    received_ping = False
    scanner_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    scanner_socket.connect((scanner.address, scanner.port))

    async def ping_responce():
        nonlocal received_ping
        while received_ping is False:
            await asyncio.sleep(0.1)

    async def state_contol_logic():
        nonlocal packet_id
        nonlocal received_ping
        nonlocal is_alive

        # async with timeout(5) as cm:

        LOGGER.info(
            f"Sending ping packet #{packet_id} to scanner #{scanner.scanner_id}"
        )
        control_packet = StateControlPacket(
            scanner_ID=scanner.scanner_id, packet_ID=packet_id
        )

        bytes_packet = build(control_packet)
        scanner_socket.send(bytes_packet)
        packet_id += 1
        packet_id %= 256

        try:
            await asyncio.wait_for(ping_responce(), timeout=PING_TIMEOUT)
        except asyncio.exceptions.TimeoutError:
            LOGGER.error("PING TIMEOUT")
            is_alive = False
        else:
            LOGGER.info("PING PACKET ACCEPTED")
            received_ping = False

        await asyncio.sleep(PING_PERIOD)

    def parse_input_message(msg: str):
        packet = StateControlPacket()
        packet.preambula = msg[0:6]
        packet.scanner_ID = msg[6:8]
        packet.packet_ID = msg[8:10]
        packet.packet_code = msg[10:11]
        packet.reserved = msg[11:]

        return packet

    async def queue_hanler():
        nonlocal received_ping

        if queue.empty():
            pass
        else:
            message = queue.get()
            LOGGER.info(f"Scanner #{scanner.scanner_id} got message: {message}")
            parsed_packet = parse_input_message(message)
            received_ping = True

    while is_alive:
        asyncio.run(state_contol_logic())
        asyncio.run(queue_hanler())

        time.sleep(0.5)

    LOGGER.error("Scanner didn't response. Fail.")
    scanner_socket.close()


@dataclass
class _Scanner:
    _info: ScannerInfo
    _process: Process
    _queue: Queue


class Server:
    def __init__(self, ip: str, port: int) -> None:
        self._queue = ServerQueue(ip, port)
        self._scanners: List[_Scanner] = []

    @property
    def connection_info(self) -> Tuple[str, int]:
        return self._queue.server.server_address

    def start_server(self) -> None:
        self._queue.start_server()
        self._register_scanners()

    def stop_server(self) -> None:
        self._queue.stop_server()

    def run_server(self) -> None:
        multiprocessing.set_start_method("spawn", force=True)

        for scanner in self._scanners:
            scanner._process.start()

        while True:
            time.sleep(1)

            while self._queue.exists():
                self.handle(self._queue.get())

    def handle(self, client_message: ClientMessage):
        LOGGER.info("Got message!")

        # LOGGER.info(f"Client thread: {client_message.client_thread}")
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

    def _register_scanners(self) -> None:

        scanners_info_list = resolve_scanners_settings()
        assert scanners_info_list is not None

        for record in scanners_info_list:

            _q: Queue = Queue()
            new_scanner = _Scanner(
                _info=record,
                _process=Process(target=scanner_process, args=(record, _q)),
                _queue=_q,
            )
            self._scanners.append(new_scanner)
