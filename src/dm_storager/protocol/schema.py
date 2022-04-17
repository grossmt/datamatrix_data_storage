from dataclasses import dataclass
from dm_storager.protocol.const import PacketCode, PRODUCT_COUNT
from typing import List, Annotated


@dataclass
class HeaderPacket:
    preambula: str
    scanner_ID: int
    packet_ID: int
    packet_code: PacketCode


@dataclass
class StateControlPacket(HeaderPacket):
    reserved: int


@dataclass
class ScannerControlResponse(StateControlPacket):
    pass


@dataclass
class ScannerSettings:
    products: Annotated[List[str], PRODUCT_COUNT]
    server_ip: str
    server_port: int
    gateway_ip: str
    netmask: str
    reserved: str


@dataclass
class SettingsSetRequest(HeaderPacket):
    settings: ScannerSettings


@dataclass
class SettingsSetResponse(HeaderPacket):
    response_code: int


@dataclass
class ArchieveData:
    records_count: int
    record_len: int
    product_id: int
    records: List[str]


@dataclass
class ArchieveDataRequest(HeaderPacket):
    archieve_data: ArchieveData


@dataclass
class ArchieveDataResponse(HeaderPacket):
    response_code: int
