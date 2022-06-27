from dataclasses import dataclass
from typing import List, Annotated

from dm_storager.protocol.const import PacketCode, ScannerSettingsDesc


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
    products: Annotated[List[str], ScannerSettingsDesc.PRODUCT_COUNT]
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
    records: List[bytes]


@dataclass
class ArchieveDataRequest(HeaderPacket):
    archieve_data: ArchieveData


@dataclass
class ArchieveDataResponse(HeaderPacket):
    response_code: int
