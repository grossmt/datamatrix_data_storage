from typing import Union, Tuple

from dm_storager.protocol.exceptions import (
    InvalidField,
    TooShortMessage,
)
from dm_storager.protocol.const import (
    # general
    ENCODING,
    BYTEORDER,
    PREAMBULA,
    PacketCode,
    MIN_MSG_LEN,
    # header
    PREAMBULA_POS,
    PREAMBULA_LEN,
    SCANNER_ID_LEN,
    SCANNER_ID_POS,
    PACKET_ID_LEN,
    PACKET_ID_POS,
    PACKET_CODE_LEN,
    PACKET_CODE_POS,
    HEADER_LEN,
)

from dm_storager.protocol.schema import (
    HeaderPacket,
    ScannerControlResponse,
    SettingsSetResponse,
    ArchieveDataRequest,
)

ParsedPacketType = Union[
    ScannerControlResponse, SettingsSetResponse, ArchieveDataRequest, None
]


def is_valid_header(msg_header: bytes) -> HeaderPacket:

    def validate_preambula(_slice: bytes) -> str:
        try:
            preambula = _slice.decode(ENCODING)
            assert preambula == PREAMBULA
            return preambula
        except Exception:
            raise InvalidField(field="Preambula", slice=_slice)

    def validate_scanner_id(_slice: bytes) -> int:
        try:
            scanner_id_int = int.from_bytes(_slice, byteorder=BYTEORDER)
            return scanner_id_int
        except Exception:
            raise InvalidField(field="Scanner ID", slice=_slice)

    def validate_packet_id(_slice: bytes) -> int:
        try:
            packet_id_int = int.from_bytes(_slice, byteorder=BYTEORDER)
            return packet_id_int
        except Exception:
            raise InvalidField(field="Packet ID", slice=_slice)

    def validate_packet_code(_slice: bytes) -> PacketCode:
        try:
            packet_code_int = int.from_bytes(_slice, byteorder=BYTEORDER)
            assert packet_code_int in PacketCode
            return packet_code_int
        except Exception:
            raise InvalidField(field="Packet Code", slice=_slice)

    new_header = HeaderPacket(
        preambula=  validate_preambula(msg_header[PREAMBULA_POS:SCANNER_ID_POS]),
        scanner_ID= validate_scanner_id(msg_header[SCANNER_ID_POS:PACKET_ID_POS]),
        packet_ID=  validate_packet_id(msg_header[PACKET_ID_POS:PACKET_CODE_POS]),
        packet_code=validate_packet_code(msg_header[PACKET_CODE_POS:]),
    )

    return new_header


def parse_state_control_response_packet(header: HeaderPacket, msg_body: bytes) -> ScannerControlResponse:
    try:
        reserved = int.from_bytes(msg_body, byteorder=BYTEORDER)
        assert reserved == 0
    except Exception:
        raise InvalidField("Reserved", msg_body)

    return ScannerControlResponse(
        header.preambula,
        header.scanner_ID,
        header.packet_ID,
        header.packet_code,
        reserved
    )


def parse_settings_set_response_packet(msg: bytes) -> ScannerControlResponse:
    pass


def parse_archieve_data(msg: bytes):
    pass


def get_packet_code(msg: bytes) -> int:
    if len(msg) < MIN_MSG_LEN:
        raise TooShortMessage(msg)

    header = is_valid_header(msg[0:HEADER_LEN])
    return header.packet_code


def get_scanner_id(msg: bytes) -> int:
    if len(msg) < MIN_MSG_LEN:
        raise TooShortMessage(msg)

    header = is_valid_header(msg[0:HEADER_LEN])
    return header.scanner_ID


def parse_input_message(
    msg: bytes,
) -> ParsedPacketType:

    packet = None

    header = is_valid_header(msg[0:HEADER_LEN])
    
    if header.packet_code == PacketCode.STATE_CONTROL_CODE:
        packet = parse_state_control_response_packet(header, msg[HEADER_LEN:])
    elif header.packet_code == PacketCode.SETTINGS_SET_CODE:
        packet = parse_settings_set_response_packet(msg)
    if header.packet_code == PacketCode.ARCHIEVE_DATA_CODE:
        packet = parse_archieve_data(msg)

    return packet
