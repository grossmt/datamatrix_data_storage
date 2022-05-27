from socket import inet_aton as ip_str_to_bytes

from typing import Union

from dm_storager.protocol.const import (
    ENCODING,
    BYTEORDER,
    SCANNER_ID_LEN,
    PACKET_ID_LEN,
    PACKET_CODE_LEN,
    STATE_CONTROL_RESERVED_LEN,
    STATE_CONTROL_PACKEN_LEN,
    PRODUCT_NAME_LEN,
    SETTINGS_RESERVED_LEN,
    SETTINGS_REQUEST_PACKET_LEN,
    ARCHIEVE_STATUS_LEN,
    ARCHIEVE_RESPONSE_LEN,
)
from dm_storager.protocol.schema import (
    StateControlRequest,
    SettingsSetRequest,
    ArchieveDataResponse,
)


def build_packet(
    packet: Union[StateControlRequest, SettingsSetRequest, ArchieveDataResponse]
) -> bytes:

    bytes_pack = bytearray()

    b_preambula = bytes(packet.preambula, ENCODING)
    # b_scanner_id = packet.scanner_ID.to_bytes(
    #     SCANNER_ID_LEN,
    #     byteorder=BYTEORDER
    # )

    b_scanner_id = bytearray.fromhex(packet.scanner_ID[2:])

    b_packet_id = packet.packet_ID.to_bytes(PACKET_ID_LEN, byteorder=BYTEORDER)
    b_packet_code = packet.packet_code.to_bytes(PACKET_CODE_LEN, byteorder=BYTEORDER)
    bytes_pack.extend(b_preambula)
    bytes_pack.extend(b_scanner_id)
    bytes_pack.extend(b_packet_id)
    bytes_pack.extend(b_packet_code)

    if isinstance(packet, StateControlRequest):
        b_reserved = packet.reserved.to_bytes(
            STATE_CONTROL_RESERVED_LEN, byteorder=BYTEORDER
        )
        bytes_pack.extend(b_reserved)
        assert len(bytes_pack) == STATE_CONTROL_PACKEN_LEN

    elif isinstance(packet, SettingsSetRequest):
        b_products = b"".join(
            list(
                map(
                    lambda x: bytes(
                        x + "".join("\x00" for i in range(PRODUCT_NAME_LEN - len(x))),
                        encoding=ENCODING,
                    ),
                    list(packet.settings.products),
                )
            )
        )
        b_server_ip = ip_str_to_bytes(packet.settings.server_ip)
        b_server_port = packet.settings.server_port.to_bytes(2, byteorder=BYTEORDER)
        b_gateway_ip = ip_str_to_bytes(packet.settings.gateway_ip)
        b_netmask = ip_str_to_bytes(packet.settings.netmask)

        b_reserved = packet.reserved.to_bytes(
            SETTINGS_RESERVED_LEN, byteorder=BYTEORDER
        )

        bytes_pack.extend(b_products)
        bytes_pack.extend(b_server_ip)
        bytes_pack.extend(b_server_port)
        bytes_pack.extend(b_gateway_ip)
        bytes_pack.extend(b_netmask)
        bytes_pack.extend(b_reserved)

        assert len(bytes_pack) == SETTINGS_REQUEST_PACKET_LEN

    elif isinstance(packet, ArchieveDataResponse):
        b_response_code = packet.response_code.to_bytes(
            ARCHIEVE_STATUS_LEN, byteorder=BYTEORDER
        )
        bytes_pack.extend(b_response_code)
        assert len(bytes_pack) == ARCHIEVE_RESPONSE_LEN

    return bytes_pack
