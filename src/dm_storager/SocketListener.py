from operator import truediv
import time
import sys

import multiprocessing
from multiprocessing import Process
from typing import Union, Optional, List
from threading import Thread

from socket import socket, AF_INET, SOCK_STREAM, SHUT_WR, SOL_SOCKET, SO_REUSEADDR
from sys import byteorder

from black import assert_equivalent

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
)


def _client_thread(connection, ip, port, max_buffer_size=5120):

    is_active = True

    while is_active:
        client_input = _receive_input(connection, max_buffer_size)

        if "--QUIT--" in client_input:
            print("Client is requesting to quit")
            connection.close()
            print("Connection " + ip + ":" + port + " closed")
            is_active = False
        else:
            print("Processed result: {}".format(client_input))
            connection.sendall("-".encode("utf8"))


def _receive_input(connection, max_buffer_size):
    client_input = connection.recv(max_buffer_size)
    client_input_size = sys.getsizeof(client_input)

    if client_input_size > max_buffer_size:
        print("The input size is greater than expected {}".format(client_input_size))

    decoded_input = client_input.decode("utf8").rstrip()  # decode and strip end of line
    result = decoded_input

    return result


class SockerHandler(object):
    def __init__(
        self,
        # scanner_address: str = SOCKET_ADDRESS,
        # port: int = SOCKET_PORT,
    ) -> None:
        self._sockets: List[socket] = []
        self._scanners: List[ScannerStat] = []

        self._client_socket = socket(AF_INET, SOCK_STREAM)
        self._client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self._client_socket.bind(("", SOCKET_PORT_LISTENER))
        self._is_open = False

    def add_scanner(self, new_scanner: ScannerStat) -> None:

        for present_scanner in self._scanners:
            if new_scanner.scanner_id == present_scanner.scanner_id:
                print("Scanner with given ID already exists!")
                return
        self._scanners.append(new_scanner)
        new_socket = socket(AF_INET, SOCK_STREAM)
        self._sockets.append(new_socket)

    def open(self, scanner: Union[ScannerStat, str]) -> None:

        if scanner == "all":
            # open all
            pass
        elif isinstance(scanner, ScannerStat):
            # open specified
            i = self._scanners.index(scanner)
            if self._scanners[i].is_open:
                print("Already opened")
                return
            self._scanners[i].packet_id = 0

            try:
                self._sockets[0].connect(
                    (self._scanners[i].address, self._scanners[i].port)
                )
                self._scanners[i].is_open = True
            except Exception as ex:
                print(str(ex))
                self._sockets[0].close()
                self._is_open = False

    async def listen(self):
        if self._is_open is True:
            print("Already listening")
            return

        # self._client_socket.shutdown(SHUT_WR)
        self._client_socket.listen(5)

        while True:
            try:
                connection, address = self._client_socket.accept()
                ip, port = str(address[0]), str(address[1])

                print("Connected with " + ip + ":" + port)
                Thread(target=_client_thread, args=(connection, ip, port)).start()
            except Exception:
                print("Thread did not start.")

        self._client_socket.close()

    async def ping(self, scanner):

        i = self._scanners.index(scanner)

        if self._scanners[i].is_open is False:
            print("Pinging closed scanner socket")
            return

        # current_packet_id = 0

        packet = StateControlPacket()
        packet.scanner_ID = self._scanners[i].scanner_id
        packet.packet_ID = self._scanners[i].packet_id

        b_packet = self._build(packet)

        while True:
            try:
                self._sockets[0].send(b_packet)
                time.sleep(SCANNER_PING_TIMEOUT)
                print(f"send to socket {b_packet}")
            except ConnectionResetError:
                print("Server closed connect")
                return False
            except Exception as ex:
                print(str(ex))
                return False

        return True

    def close(self) -> None:
        if self._is_open:
            self._sockets[0].close()
        self._is_open = False

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
