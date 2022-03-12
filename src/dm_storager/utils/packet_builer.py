from typing import Union

from dm_storager.structs import (
    StateControlPacket,
    SettingsSetRequestPacket
)


def build_packet(packet: Union[StateControlPacket, SettingsSetRequestPacket]) -> bytes:

    bytes_pack = bytearray()

    if isinstance(packet, StateControlPacket):
        b_preambula = bytes(packet.preambula, "cp1251")
        b_scanner_id = packet.scanner_ID.to_bytes(
            packet.scanner_ID_len, byteorder="big"
        )
        b_packet_id = packet.packet_ID.to_bytes(packet.packet_ID_len, byteorder="big")
        b_packet_code = packet.packet_code.to_bytes(
            packet.packet_code_len, byteorder="big"
        )
        b_reserved = packet.reserved.to_bytes(packet.reserved_len, byteorder="big")

        bytes_pack.extend(b_preambula)
        bytes_pack.extend(b_scanner_id)
        bytes_pack.extend(b_packet_id)
        bytes_pack.extend(b_packet_code)
        bytes_pack.extend(b_reserved)

        bytes_pack.extend(b"\x13")
        # assert_equivalent(len(bytes_pack), packet.packet_size)
    elif isinstance(packet, SettingsSetRequestPacket):
        pass
    else:
        raise

    return bytes_pack
