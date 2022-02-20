from operator import truediv
from struct import pack
import time

import os

import multiprocessing
import logging

from multiprocessing import Process
from typing import Union, Optional, List
from threading import Thread

from socket import socket, AF_INET, SOCK_STREAM, SHUT_WR, SOL_SOCKET, SO_REUSEADDR
from sys import byteorder

# from black import assert_equivalent

from dm_storager.const import (
    SOCKET_ADDRESS,
    SOCKET_PORT_SERVER,
    SOCKET_PORT_LISTENER,
    DEFAULT_SCANNER_ID,
    SCANNER_PING_TIMEOUT,
)

from dm_storager.structs import (
    StateControlPacket,
    SettingsSetRequestPacket,
    ScannerStat,
    ScannerHandler,
)

# from dm_storager.__main__ import LOGGER
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


def listening_thread(connection, ip, port):

    is_active = True

    while is_active:

        def process_input(connection, max_buffer_size=5120) -> Optional[str]:
            b_scanner_packet = connection.recv(max_buffer_size)
            scanner_packet = b_scanner_packet.decode(
                "utf8"
            ).rstrip()  # decode and strip end of line
            return scanner_packet

        def parse_input(message: str) -> Union[StateControlPacket, None]:
            packet = StateControlPacket()
            packet.preambula = message[0:6]
            packet.scanner_ID = message[6:8]
            packet.packet_ID = message[8:10]
            packet.packet_code = message[10:11]
            packet.reserved = message[11:]

            return packet

        scanner_packet = process_input(connection)

        if scanner_packet:
            LOGGER.info(f"Got connect from {ip}:{port}")
            LOGGER.debug(f"Processed result: {scanner_packet}")

            packet = parse_input(scanner_packet)

            pass


def test_process(scanner: ScannerHandler):
    pid = os.getpid()
    print(f"Scanner #{scanner.scanner.scanner_id}, process: {pid}")

    scanner.is_open = False
    scanner.scanner.packet_id = 0

    # scanner.scanner_server_socket.connect(
    #     (scanner.scanner.address, scanner.scanner.port)
    # )

    scanner.scanner_client_socket.listen(1)

    connection, address = scanner.scanner_client_socket.accept()
    ip, port = str(address[0]), str(address[1])

    print(f"Got connection from {ip}:{port}")

    b_scanner_packet = connection.recv(1024)
    scanner_packet = b_scanner_packet.decode("utf8").rstrip()
    print(f"Processed result: {scanner_packet}")
    # connection.close()
    # connection.connect()
    # connection.listen()
    time.sleep(1)

    pass


class SocketHandler(object):
    def __init__(
        self,
    ) -> None:
        self._scanners: List[ScannerStat] = []

        self._server_sockets: List[socket] = []

        self._client_socket = socket(AF_INET, SOCK_STREAM)
        self._client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self._client_socket.bind(("", SOCKET_PORT_LISTENER))

        self._is_open = False

        #

        self._scanners_handlers: List[ScannerHandler] = []

    def add_scanner(self, new_scanner: ScannerStat) -> None:

        present_scanners = [x.scanner.scanner_id for x in self._scanners_handlers]

        if new_scanner.scanner_id in present_scanners:
            LOGGER.warning("Scanner with given ID already exists!")
            return

        new_server_socket = socket(AF_INET, SOCK_STREAM)

        new_client_socket = socket(AF_INET, SOCK_STREAM)
        new_client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        new_client_socket.bind(("", SOCKET_PORT_LISTENER))

        sh = ScannerHandler(
            scanner=new_scanner,
            scanner_client_socket=new_client_socket,
            scanner_server_socket=new_server_socket,
            is_open=False,
            pid=None,
        )

        self._scanners_handlers.append(sh)

    async def run_scanner(self, scanner: ScannerHandler) -> None:
        multiprocessing.set_start_method("spawn", force=True)
        Process(target=test_process, args=(scanner,)).start()

    def open(self, scanner: ScannerStat) -> None:
        i = self._scanners.index(scanner)
        if self._scanners[i].is_open:
            LOGGER.warning(f"Scanner #{scanner.scanner_id} was already opened")
            return

        self._scanners[i].packet_id = 0

        try:
            self._scanners[i].scanner_socket.connect(
                (self._scanners[i].address, self._scanners[i].port)
            )
            self._scanners[i].is_open = True
        except TimeoutError:
            LOGGER.error("Timeout on scanner connection")
            LOGGER.error(f"Scanner id: {self._scanners[i].scanner_id}")
            LOGGER.error(f"Scanner address: {self._scanners[i].address}")
            LOGGER.error(f"Scanner port: {self._scanners[i].port}")

        except Exception as ex:
            LOGGER.error("An exception occurs during socket opening:")
            LOGGER.error(f"Scanner id: {self._scanners[i].scanner_id}")
            LOGGER.error(f"Scanner address: {self._scanners[i].address}")
            LOGGER.error(f"Scanner port: {self._scanners[i].port}")
            LOGGER.error(str(ex))
            self._scanners[i].scanner_socket.close()

    async def listen(self):
        if self._is_open is True:
            LOGGER.warning("Already listening")
            return

        self._client_socket.listen(MAX_SCANNERS_COUNT)

        while True:
            try:
                connection, address = self._client_socket.accept()
                ip, port = str(address[0]), str(address[1])
                LOGGER.info(f"Got connection from {ip}:{port}")
                Thread(target=listening_thread, args=(connection, ip, port)).start()
            except Exception as ex:
                LOGGER.error("Server thread did not started.")
                LOGGER.error(f"Reason: {str(ex)}")
                continue

        self._client_socket.close()

    async def ping(self, scanner):

        i = self._scanners.index(scanner)
        given_scaner = self._scanners[i]
        if given_scaner.is_open is False:
            LOGGER.warning("Trying to ping closed scanner.")
            LOGGER.warning(f"Scanner ID: {self._scanners[i].scanner_id}")
            LOGGER.warning(f"Scanner Address: {self._scanners[i].address}")
            LOGGER.warning(f"Scanner Port: {self._scanners[i].port}")
            return

        packet = StateControlPacket()
        packet.scanner_ID = given_scaner.scanner_id
        packet.packet_ID = given_scaner.packet_id

        bytes_packet = self._build(packet)

        while True:
            try:
                # self._server_sockets[0].send(bytes_packet)
                given_scaner.scanner_socket.send(bytes_packet)
                LOGGER.debug(f"Ping of scanner {given_scaner.scanner_id}")
                LOGGER.debug(f"Send to socket {bytes_packet}")

                time.sleep(SCANNER_PING_TIMEOUT)

            except ConnectionResetError as ex:
                LOGGER.error("Server closed connect")
                LOGGER.error(f"Reason: {str(ex)}")
                return False
            except Exception as ex:
                print(str(ex))
                return False

        return True

    def close(self) -> None:
        pass

    def _build(
        self, packet: Union[StateControlPacket, SettingsSetRequestPacket]
    ) -> bytes:

        bytes_pack = bytearray()

        if isinstance(packet, StateControlPacket):
            b_preambula = bytes(packet.preambula, "cp1251")
            b_scanner_id = packet.scanner_ID.to_bytes(
                packet.scanner_ID_len, byteorder="big"
            )
            b_packet_id = packet.packet_ID.to_bytes(
                packet.packet_ID_len, byteorder="big"
            )
            b_packet_code = packet.packet_code.to_bytes(
                packet.packet_code_len, byteorder="big"
            )
            b_reserved = packet.reserved.to_bytes(packet.reserved_len, byteorder="big")

            bytes_pack.extend(b_preambula)
            bytes_pack.extend(b_scanner_id)
            bytes_pack.extend(b_packet_id)
            bytes_pack.extend(b_packet_code)
            bytes_pack.extend(b_reserved)

            # assert_equivalent(len(bytes_pack), packet.packet_size)
        elif isinstance(packet, SettingsSetRequestPacket):
            pass
        else:
            raise

        return bytes_pack
