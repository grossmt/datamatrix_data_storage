from dataclasses import dataclass
from socket import socket
from multiprocessing import Process, Queue
from typing import Dict, Optional, Union, Any
from pydantic import BaseModel, conlist
from threading import Thread


Products = conlist(str, min_items=6, max_items=6)
ScannerName = str
PropertyName = str


class NetworkSettings(BaseModel):
    """Connection pair."""

    host: str
    port: int


class ScannerInfo(BaseModel):
    """General scanner info."""

    name: str
    description: Optional[str]
    address: str


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


@dataclass
class ClientMessage:
    client_thread: Thread
    client_ip: str
    client_port: int
    client_message: bytes
