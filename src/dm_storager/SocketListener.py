from operator import truediv
import time
import multiprocessing
from multiprocessing import Process
from typing import Union, Optional, List

from socket import socket, AF_INET, SOCK_STREAM
from sys import byteorder

from black import assert_equivalent

from dm_storager.const import (
    SOCKET_ADDRESS,
    SOCKET_PORT,
    DEFAULT_SCANNER_ID,
    SCANNER_PING_TIMEOUT,
)

from dm_storager.structs import (
    StateControlPacket,
    SettingsSetRequestPacket,
    ScannerStat,
)


def run_ping_in_proc():
    print("Sleep for 2 sec")
    time.sleep(2)


class SockerHandler(object):
    def __init__(
        self,
        # scanner_address: str = SOCKET_ADDRESS,
        # port: int = SOCKET_PORT,
    ) -> None:
        self._sockets: List[socket] = []
        self._is_open = False
        self._scanners: List[ScannerStat] = []

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
        if self._is_open is False:
            return

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
