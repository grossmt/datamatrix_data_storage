from dataclasses import dataclass
from enum import Enum
from socket import socket
from threading import Thread
from typing import Optional

from dm_storager.const import (
    PREAMBULA,
    STATE_CONTROL_CODE,
    STATE_CONTROL_RESERVED,
    SETTINGS_SET_CODE,
)


class SettingsError(Enum):
    OK = b"\x00\x00\x00\x00"


@dataclass
class SettingsData:
    product_name: str = ""  # 32 bytes
    scanner_ip: str = ""  # 4 bytes
    scanner_port: int = 0  # 2 bytes
    gateway_port: str = ""  # 4 bytes
    network_mask: str = ""  # 4 bytes
    listener_ip: str = ""  # 4 bytes
    reserved: str = ""  # 46 bytes


@dataclass
class HeaderPacket:
    preambula: str = PREAMBULA
    scanner_ID: int = 0
    scanner_ID_len: int = 2
    packet_ID: int = 0
    packet_ID_len: int = 2


@dataclass
class StateControlPacket(HeaderPacket):
    packet_code: int = STATE_CONTROL_CODE
    packet_code_len: int = 1
    reserved: int = STATE_CONTROL_RESERVED
    reserved_len: int = 4
    packet_size: int = 15


@dataclass
class SettingsSetRequestPacket(HeaderPacket):
    packet_code: bytes = SETTINGS_SET_CODE
    settings_data: SettingsData = SettingsData()


@dataclass
class SettingsSetResponse(HeaderPacket):
    packet_code: bytes = SETTINGS_SET_CODE
    settings_response: SettingsError = SettingsError.OK


@dataclass
class ScannerInfo:
    address: str
    port: int
    scanner_id: int

@dataclass
class ScannerHandler:
    scanner_info: ScannerInfo
    scanner_socket: Optional[socket] = None

    packet_id: int = 0
    is_open: bool = False
    scanner_thread: Optional[Thread] = None

@dataclass 
class ClientMessage:
    client_thread: Thread
    client_ip: str
    client_port: int
    client_message: str
