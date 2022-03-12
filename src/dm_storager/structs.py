from dataclasses import dataclass
from threading import Thread
from multiprocessing import Process, Queue


@dataclass 
class ClientMessage:
    client_thread: Thread
    client_ip: str
    client_port: int
    client_message: str

@dataclass
class ScannerInfo:
    address: str
    port: int
    scanner_id: int
    
@dataclass
class Scanner:
    info: ScannerInfo
    process: Process
    queue: Queue