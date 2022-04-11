from dataclasses import dataclass
from threading import Thread
from multiprocessing import Process, Queue
from typing import Optional, List


@dataclass
class ClientMessage:
    client_thread: Thread
    client_ip: str
    client_port: int
    # client_message: str
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
    process: Process
    queue: Queue


@dataclass
class ScannerSettings:
    products: List[str]
    server_ip: str
    server_port: int
    gateway_ip: str
    netmask: str
