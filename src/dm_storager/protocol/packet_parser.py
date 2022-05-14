from typing import List, Union, Tuple

from dm_storager.protocol.exceptions import (
    InvalidField,
    TooShortMessage,
)
from dm_storager.protocol.const import (
    # general
    ENCODING,
    BYTEORDER,
    PREAMBULA,
    RECORD_COUNT_LEN,
    RECORD_COUNT_POS,
    RECORD_PRODUCT_ID_LEN,
    RECORD_PRODUCT_ID_POS,
    RECORD_SINGLE_LEN,
    RECORD_SINGLE_POS,
    RECORDS_START_POS,
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
    STATE_CONTROL_RESERVED_LEN,
    SETTINGS_APPLY_STATUS_LEN,
)

from dm_storager.protocol.schema import (
    ArchieveData,
    HeaderPacket,
    ScannerControlResponse,
    SettingsSetResponse,
    ArchieveDataRequest,
)
from dm_storager.protocol.utils import format_hex_bytes

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

    def validate_scanner_id(_slice: bytes) -> str:
        try:
            # scanner_id_int = int.from_bytes(_slice, byteorder=BYTEORDER)
            scanner_id_hex = format_hex_bytes(_slice)
            return scanner_id_hex
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
            assert PacketCode.has_value(packet_code_int) is True
            return packet_code_int  # type: ignore
        except Exception:
            raise InvalidField(field="Packet Code", slice=_slice)

    new_header = HeaderPacket(
        preambula=validate_preambula(msg_header[PREAMBULA_POS:SCANNER_ID_POS]),
        scanner_ID=validate_scanner_id(msg_header[SCANNER_ID_POS:PACKET_ID_POS]),
        packet_ID=validate_packet_id(msg_header[PACKET_ID_POS:PACKET_CODE_POS]),
        packet_code=validate_packet_code(msg_header[PACKET_CODE_POS:]),
    )

    return new_header


def parse_state_control_response_packet(
    header: HeaderPacket, msg_body: bytes
) -> ScannerControlResponse:
    try:
        assert len(msg_body) == STATE_CONTROL_RESERVED_LEN
        reserved = int.from_bytes(msg_body, byteorder=BYTEORDER)
        assert reserved == 0
    except Exception:
        raise InvalidField("Reserved", msg_body)

    return ScannerControlResponse(
        header.preambula,
        header.scanner_ID,
        header.packet_ID,
        header.packet_code,
        reserved,
    )


def parse_settings_set_response_packet(
    header: HeaderPacket, msg_body: bytes
) -> SettingsSetResponse:

    try:
        assert len(msg_body) == SETTINGS_APPLY_STATUS_LEN
        response_code = int.from_bytes(msg_body, byteorder=BYTEORDER)
    except Exception:
        raise InvalidField("Settings set response code", msg_body)

    return SettingsSetResponse(
        header.preambula,
        header.scanner_ID,
        header.packet_ID,
        header.packet_code,
        response_code,
    )


def parse_archieve_data(header: HeaderPacket, msg_body: bytes) -> ArchieveDataRequest:
    def validate_records_count(msg_slice: bytes) -> int:
        try:
            return int.from_bytes(msg_slice, byteorder=BYTEORDER)
        except Exception:
            raise InvalidField("Archieve data records count", msg_slice)

    def validate_single_record_len(msg_slice: bytes) -> int:
        try:
            return int.from_bytes(msg_slice, byteorder=BYTEORDER)
        except Exception:
            raise InvalidField("Archieve data single record lenght", msg_slice)

    def validate_record_product_id(msg_slice: bytes) -> int:
        try:
            return int.from_bytes(msg_slice, byteorder=BYTEORDER)
        except Exception:
            raise InvalidField("Archieve data record product id", msg_slice)

    try:
        assert len(msg_body) > (
            RECORD_COUNT_LEN + RECORD_SINGLE_LEN + RECORD_PRODUCT_ID_LEN
        )
    except AssertionError:
        raise TooShortMessage(None, msg_body)

    records_count = validate_records_count(
        msg_body[RECORD_COUNT_POS : RECORD_COUNT_POS + RECORD_COUNT_LEN]
    )
    single_record_len = validate_single_record_len(
        msg_body[RECORD_SINGLE_POS : RECORD_SINGLE_POS + RECORD_SINGLE_LEN]
    )
    record_product_id = validate_record_product_id(
        msg_body[RECORD_PRODUCT_ID_POS : RECORD_PRODUCT_ID_POS + RECORD_PRODUCT_ID_LEN]
    )

    records: List[str] = []
    msg_body = msg_body[RECORDS_START_POS:]

    try:
        assert len(msg_body) == records_count * single_record_len
    except AssertionError:
        raise TooShortMessage(
            expected_len=records_count * single_record_len, slice=msg_body
        )

    for i in range(records_count):
        b_record = msg_body[:single_record_len]
        try:
            record = b_record.decode(ENCODING)
        except Exception:
            raise InvalidField("Archieve data record", b_record)
        records.append(record)
        msg_body = msg_body[single_record_len:]

    archieve_data = ArchieveData(
        records_count, single_record_len, record_product_id, records
    )

    return ArchieveDataRequest(
        header.preambula,
        header.scanner_ID,
        header.packet_ID,
        header.packet_code,
        archieve_data,
    )


def get_packet_code(msg: bytes) -> int:
    if len(msg) < MIN_MSG_LEN:
        raise TooShortMessage(None, msg)

    header = is_valid_header(msg[0:HEADER_LEN])
    return header.packet_code


def get_scanner_id(msg: bytes) -> str:
    if len(msg) < MIN_MSG_LEN:
        raise TooShortMessage(None, msg)

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
        packet = parse_settings_set_response_packet(header, msg[HEADER_LEN:])
    if header.packet_code == PacketCode.ARCHIEVE_DATA_CODE:
        packet = parse_archieve_data(header, msg[HEADER_LEN:])

    return packet


# good = b'RFLABC\x01\x01\x01\x01\x45\x02\x00\x08\x01PRODUCT1PRODUCT2'
# bad_pream = b'RFLAC\x01\x01\x01\x01\x45\x02\x00\x08\x01PRODUCT1PRODUCT2'
# bad_packet_code= b'RFLABC\x91\xFF\x01\x01\x47\x02\x00\x08\x01PRODUCT1PRODUCT2'

# bad_record_len = b'RFLABC\x01\x01\x01\x01\x45\x02\x00\x09\x01PRODUCT1PRODUCT2'
# bad_products = b'RFLABC\x01\x01\x01\x01\x45\x02\x00\x08\x01PRODUCT1PRODU'
# bad_products2 = b'RFLABC\x01\x01\x01\x01\x45\x02\x00\x08'

# try:
#     result = parse_input_message(good)
#     # result = parse_input_message(bad_pream)
#     # result = parse_input_message(bad_packet_code)
#     # result = parse_input_message(bad_record_len)
#     # result = parse_input_message(bad_products)
#     result = parse_input_message(bad_products2)
# except Exception:
#     pass

# pass
