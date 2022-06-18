from dataclasses import dataclass
from socket import socket
from multiprocessing import Process, Queue
from typing import Dict, Optional, Union, Any
from pydantic import BaseModel, conlist
from threading import Thread

from enum import auto
from strenum import StrEnum

Products = conlist(str, min_items=6, max_items=6)
ScannerName = str
PropertyName = str


class FileFormat(StrEnum):
    TXT = auto()
    CSV = auto()


class NetworkSettings(BaseModel):
    """Connection pair."""

    host: str
    port: int


class ScannerInfo(BaseModel):
    """General scanner info."""

    name: str
    description: Optional[str]
    address: str
    # data_format: Optional[FileFormat]
    # update_setttings_on_connect: bool


class ScannerInternalSettings(BaseModel):
    """Scanner internal settings."""

    products: Products
    server_ip: str
    server_port: int
    gateway_ip: str
    netmask: str


@dataclass
class ScannerRuntimeSettings:
    """Scanner runtime propertiess."""

    port: Optional[int]
    process: Optional[Process]
    queue: Optional[Queue]
    client_socket: Optional[socket]


ScannerSettings = Dict[
    ScannerName,
    Dict[
        PropertyName,
        Union[ScannerInfo, ScannerInternalSettings, Any],
    ],
]


class Config(BaseModel):
    """Configuration of server and registered clients."""

    title: str
    subtitle: Optional[str]
    debug_flag: Optional[str]
    server: NetworkSettings
    scanners: ScannerSettings


@dataclass
class Scanner:
    """Scanner connection settings."""

    scanner_id: str
    info: ScannerInfo
    settings: ScannerInternalSettings
    runtime: ScannerRuntimeSettings


@dataclass
class HandshakeMessage:
    client_socket: socket
    client_ip: str
    client_port: int
    client_socket_thread: Thread


@dataclass
class ClientMessage:
    client_socket_thread: Thread
    client_ip: str
    client_port: int
    client_message: bytes


ThreadList = Dict[ScannerName, Thread]
