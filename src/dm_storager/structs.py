from dataclasses import dataclass
from socket import socket
from threading import Thread
from multiprocessing import Process, Queue
from typing import Optional, List


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


@dataclass
class ScannerInfo:
    name: str
    address: str
    port: Optional[int]
    scanner_id: int


@dataclass
class Scanner:
    info: ScannerInfo
    process: Optional[Process]
    queue: Queue
    client_socket: Optional[socket]

@dataclass
class ScannerSettings:
    products: List[Optional[str]]
    server_ip: Optional[str]
    server_port: Optional[int]
    gateway_ip: Optional[str]
    netmask: Optional[str]
