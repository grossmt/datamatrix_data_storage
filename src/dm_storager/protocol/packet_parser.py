from typing import Union, Tuple

from dm_storager.exceptions import (
    TooShortMessage,
    InvalidPreambula,
    InvalidScannerID,
    InvalidPacketCode,
    InvalidPacketID,
)
from dm_storager.protocol.const import (
    # general
    ENCODING,
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
    ScannerControlResponse,
    SettingsSetResponse,
    ArchieveDataRequest,
)

ParsedPacketType = Union[
    ScannerControlResponse, SettingsSetResponse, ArchieveDataRequest, None
]


def is_valid_header(msg_header: bytes) -> bool:
    def validate_preambula(_slice: bytes):
        try:
            preambula = _slice.decode(ENCODING)
            assert preambula == PREAMBULA
        except Exception:
            raise InvalidPreambula(_slice)

    def validate_scanner_id(_slice: bytes):
        try:
            scanner_id_int = int.from_bytes(_slice, byteorder="big")  # noqa: F841
        except Exception:
            raise InvalidScannerID(_slice)

    def validate_packet_id(_slice: bytes):
        try:
            packet_id_int = int.from_bytes(_slice, byteorder="big")  # noqa: F841
        except Exception:
            raise InvalidPacketID(_slice)

    def validate_packet_code(_slice: bytes):
        try:
            packet_code_int = int.from_bytes(_slice, byteorder="big")
            assert packet_code_int in PacketCode
        except Exception:
            raise InvalidPacketCode(_slice)

    validate_preambula(msg_header[PREAMBULA_POS:SCANNER_ID_POS])
    validate_scanner_id(msg_header[SCANNER_ID_POS:PACKET_ID_POS])
    validate_packet_id(msg_header[PACKET_ID_POS:PACKET_CODE_POS])
    validate_packet_code(msg_header[PACKET_CODE_POS:])

    return True


def is_valid_body(packet_code: int, msg_body: bytes) -> bool:
    return True


def is_valid_state_control_message(msg_body: bytes) -> bool:
    pass
    return True


def parse_state_control_response_packet(msg: bytes) -> ScannerControlResponse:

    b_preambula: bytes = msg[0:PREAMBULA_LEN]
    preambula = b_preambula.decode(ENCODING)
    if preambula != PREAMBULA:
        raise

    b_scanner_id: bytes = msg[PREAMBULA_LEN : PREAMBULA_LEN + SCANNER_ID_LEN]

    packet = ScannerControlResponse(
        preambula,
    )

    pass


def parse_settings_set_response_packet(msg: bytes) -> ScannerControlResponse:
    pass


def parse_archieve_data(msg: bytes):
    pass


def is_valid_msg(msg: bytes) -> bool:

    if is_valid_header(msg[0:HEADER_LEN]):
        packet_code = get_packet_code(msg)
        return is_valid_body(packet_code, msg[HEADER_LEN:])
    return False


def get_packet_code(msg: bytes) -> int:

    packet_code_int = PacketCode.ERROR_CODE

    if len(msg) < MIN_MSG_LEN:
        raise TooShortMessage(msg)

    if is_valid_header(msg[0:HEADER_LEN]):
        b_packet_code = msg[PACKET_CODE_POS : PACKET_CODE_POS + PACKET_CODE_LEN]
        packet_code_int = int.from_bytes(b_packet_code, byteorder="big")

    return packet_code_int


def get_scanner_id(msg: bytes) -> int:
    scanner_id_int = 0

    if len(msg) < MIN_MSG_LEN:
        raise TooShortMessage(msg)

    if is_valid_header(msg[0:HEADER_LEN]):
        b_scanner_id = msg[SCANNER_ID_POS : SCANNER_ID_POS + SCANNER_ID_LEN]
        scanner_id_int = int.from_bytes(b_scanner_id, byteorder="big")

    return scanner_id_int


def parse_input_message(
    msg: bytes,
) -> ParsedPacketType:

    packet = None

    packet_code = get_packet_code(msg)

    if packet_code == PacketCode.STATE_CONTROL_CODE:
        packet = parse_state_control_response_packet(msg)
    elif packet_code == PacketCode.SETTINGS_SET_CODE:
        packet = parse_settings_set_response_packet(msg)
    if packet_code == PacketCode.ARCHIEVE_DATA_CODE:
        packet = parse_archieve_data(msg)

    return packet
