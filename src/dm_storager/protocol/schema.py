from dataclasses import dataclass
from dm_storager.protocol.const import PacketCode, PRODUCT_COUNT
from typing import List, Annotated


@dataclass
class HeaderPacket:
    preambula: str
    scanner_ID: str
    packet_ID: int
    packet_code: PacketCode


@dataclass
class StateControlRequest(HeaderPacket):
    reserved: int


@dataclass
class ScannerControlResponse(StateControlRequest):
    pass


@dataclass
class ScannerSettings:
    products: Annotated[List[str], PRODUCT_COUNT]
    server_ip: str
    server_port: int
    gateway_ip: str
    netmask: str
    reserved: int


@dataclass
class SettingsSetRequest(HeaderPacket):
    settings: ScannerSettings
    reserved: int


@dataclass
class SettingsSetResponse(HeaderPacket):
    response_code: int


@dataclass
class ArchieveData:
    product_id: int
    message_len: int
    records_count: int
    records: List[str]


@dataclass
class ArchieveDataRequest(HeaderPacket):
    archieve_data: ArchieveData


@dataclass
class ArchieveDataResponse(HeaderPacket):
    response_code: int
