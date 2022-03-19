from dataclasses import dataclass

# from dm_storager.const import (
#     PREAMBULA,
#     STATE_CONTROL_CODE,
#     STATE_CONTROL_RESERVED,
#     SETTINGS_SET_CODE,
# )


PREAMBULA = "RFLABC"

STATE_CONTROL_CODE = 0x37
STATE_CONTROL_RESERVED = 0x00
SETTINGS_SET_CODE = 0x13
ARCHIEVE_DATA_CODE = 0x45


@dataclass
class HeaderPacket:
    preambula: str = PREAMBULA
    scanner_ID: int = 0
    scanner_ID_len: int = 2
    packet_ID: int = 0
    packet_ID_len: int = 2


@dataclass
class SettingsData(HeaderPacket):
    product_name: str = ""  # 32 bytes
    scanner_ip: str = ""  # 4 bytes
    scanner_port: int = 0  # 2 bytes
    gateway_port: str = ""  # 4 bytes
    network_mask: str = ""  # 4 bytes
    listener_ip: str = ""  # 4 bytes
    reserved: str = ""  # 46 bytes


@dataclass
class StateControlPacket(HeaderPacket):
    packet_code: int = STATE_CONTROL_CODE
    packet_code_len: int = 1
    reserved: int = STATE_CONTROL_RESERVED
    reserved_len: int = 4
    packet_size: int = 15


@dataclass
class ScannerControlResponse:
    preambula: str
    scanner_id: int
    packet_code: int
    packet_id: int


@dataclass
class SettingsSetResponse:
    preambula: str
    scanner_id: int
    packet_code: int
    packet_id: int
    response_code: int


@dataclass
class ArchieveDataResponce:
    preambula: str
    scanner_id: int
    packet_code: int
    packet_id: int
    archieve_data: str
