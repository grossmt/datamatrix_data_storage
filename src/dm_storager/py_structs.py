from dataclasses import dataclass
import toml
from pathlib import Path
from socket import socket
from multiprocessing import Process, Queue
from typing import Dict, Optional, Union
from pydantic import BaseModel, conlist

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
    scanner_id: int
    address: str
    port: Optional[int]


class ScannerInternalSettings(BaseModel):
    """Scanner internal settings."""

    products: Products
    server_ip: str
    server_port: int
    gateway_ip: str
    netmask: str


ClientSettings = Dict[
    ScannerName,
    Dict[PropertyName, Union[ScannerInfo, ScannerInternalSettings]],
]


class Config(BaseModel):
    """Configuration of server and registered clients."""

    title: str
    subtitle: str
    server: NetworkSettings
    clients: ClientSettings


def load_config(path_to_config_file: Path) -> Config:
    config_dict = toml.load(path_to_config_file)
    return Config(**config_dict)


@dataclass
class ScannerRuntimeSettings:
    """Scanner runtime propertiess."""

    process: Optional[Process]
    queue: Optional[Queue]
    client_socket: Optional[socket]


@dataclass
class Scanner:
    """Scanner connection settings."""

    info: ScannerInfo
    settings: ScannerInternalSettings
    runtime: Optional[ScannerRuntimeSettings]
