from sys import byteorder
import time

from dm_storager.SocketListener import SockerHandler
from dm_storager.structs import StateControlPacket, ScannerStat
import asyncio

if __name__ == "__main__":

    print("Start of programm")
    scanners_handler = SockerHandler()

    moro_scanner = ScannerStat(address="192.168.1.58", port=5001, scanner_id=0x01)
    moro_big_scanner = ScannerStat(address="192.168.1.10", port=5001, scanner_id=0x02)

    # scanners_handler.add_scanner(moro_scanner)
    scanners_handler.add_scanner(moro_big_scanner)

    # scanners_handler.open("all")
    # scanners_handler.open(moro_scanner)
    scanners_handler.open(moro_big_scanner)

    # asyncio.run(scanners_handler.ping(moro_scanner))
    asyncio.run(scanners_handler.ping(moro_big_scanner))

    pass
