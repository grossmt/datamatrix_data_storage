from binascii import hexlify
from socket import inet_aton as ip_str_to_bytes

from typing import Union

from dm_storager.utils.logger import configure_logger

from dm_storager.protocol.schema import (
    StateControlRequest,
    SettingsSetRequest,
    ArchieveDataResponse,
)
from dm_storager.protocol.const import (
    ProtocolDesc,
    HeaderDesc,
    StateControlDesc,
    ScannerSettingsDesc,
    ArchieveDataDesc,
)

PacketType = Union[StateControlRequest, SettingsSetRequest, ArchieveDataResponse]


class PacketBuilder:
    def __init__(self, debug: bool = False) -> None:
        self._logger = configure_logger("MGS_BUILDER", debug)
        self._formatter_raw_msg: str = ""

    def build_packet(self, packet: PacketType) -> bytes:

        bytes_pack = self._build_header(packet)

        if isinstance(packet, StateControlRequest):
            bytes_pack.extend(self._build_state_control_body(packet))

        elif isinstance(packet, SettingsSetRequest):
            bytes_pack.extend(self._build_settings_body(packet))

        elif isinstance(packet, ArchieveDataResponse):
            bytes_pack.extend(self._build_archieve_data_response_body(packet))

        self._formatter_raw_msg = self._format_byte_string(bytes_pack)
        self._logger.debug("Formatted raw message:")
        self._logger.debug(f"\t{self._formatter_raw_msg}")

        return bytes_pack

    def _build_header(self, packet: PacketType) -> bytearray:

        b_header = bytearray()

        b_preambula = bytes(packet.preambula, ProtocolDesc.ENCODING)
        b_scanner_id = bytearray.fromhex(packet.scanner_ID[2:])  # 0x01 -> \x01
        b_packet_id = packet.packet_ID.to_bytes(
            HeaderDesc.PACKET_ID_LEN, byteorder=ProtocolDesc.BYTEORDER
        )
        b_packet_code = packet.packet_code.to_bytes(
            HeaderDesc.PACKET_CODE_LEN, byteorder=ProtocolDesc.BYTEORDER
        )

        b_header.extend(b_preambula)
        b_header.extend(b_scanner_id)
        b_header.extend(b_packet_id)
        b_header.extend(b_packet_code)

        return b_header

    def _build_state_control_body(self, packet: StateControlRequest) -> bytearray:
        b_body = bytearray()

        b_reserved = packet.reserved.to_bytes(
            StateControlDesc.RESERVED_LEN,
            byteorder=ProtocolDesc.BYTEORDER,
        )
        b_body.extend(b_reserved)
        return b_body

    def _build_settings_body(self, packet: SettingsSetRequest) -> bytearray:
        b_body = bytearray()

        b_products = b"".join(
            list(
                map(
                    lambda x: bytes(
                        x
                        + "".join(
                            "\x00"
                            for i in range(
                                ScannerSettingsDesc.PRODUCT_NAME_LEN - len(x)
                            )
                        ),
                        encoding=ProtocolDesc.ENCODING,
                    ),
                    list(packet.settings.products),
                )
            )
        )
        b_server_ip = ip_str_to_bytes(packet.settings.server_ip)
        b_server_port = packet.settings.server_port.to_bytes(
            2, byteorder=ProtocolDesc.BYTEORDER
        )
        b_gateway_ip = ip_str_to_bytes(packet.settings.gateway_ip)
        b_netmask = ip_str_to_bytes(packet.settings.netmask)

        b_reserved = packet.reserved.to_bytes(
            ScannerSettingsDesc.RESERVED_LEN, byteorder=ProtocolDesc.BYTEORDER
        )

        b_body.extend(b_products)
        b_body.extend(b_server_ip)
        b_body.extend(b_server_port)
        b_body.extend(b_gateway_ip)
        b_body.extend(b_netmask)
        b_body.extend(b_reserved)

        return b_body

    def _build_archieve_data_response_body(
        self, packet: ArchieveDataResponse
    ) -> bytearray:
        b_body = bytearray()

        b_response_code = packet.response_code.to_bytes(
            ArchieveDataDesc.RESPONSE_CODE_LEN, byteorder=ProtocolDesc.BYTEORDER
        )
        b_body.extend(b_response_code)

        return b_body

    def _format_byte_string(self, byte_str: bytes) -> str:
        return str(repr(hexlify(byte_str, "-"))[2:-1]).replace("\\x", "")  # noqa:WPS221
