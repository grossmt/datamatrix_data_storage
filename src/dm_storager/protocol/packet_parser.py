from functools import wraps
from typing import Callable, List, Union, Tuple, Optional

from dm_storager.protocol.exceptions import (
    InvalidField,
    TooShortMessage,
)
from dm_storager.protocol.const import (
    ProtocolDesc,
    HeaderDesc,
    StateControlDesc,
    ArchieveDataDesc,
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
    def validate_int_field(
        field: str,
        msg_slice: bytes,
    ) -> int:
        try:
            return int.from_bytes(msg_slice, byteorder=BYTEORDER)
        except Exception:
            raise InvalidField(f"Archieve data record {field}", msg_slice)

    product_id = validate_int_field(
        field="product id",
        msg_slice=msg_body[
            ArchieveDataDesc.PRODUCT_CODE_POS : ArchieveDataDesc.PRODUCT_CODE_POS
            + ArchieveDataDesc.PRODUCT_CODE_LEN
        ],
    )

    msg_len = validate_int_field(
        field="message size",
        msg_slice=msg_body[
            ArchieveDataDesc.MGS_SIZE_POS : ArchieveDataDesc.MGS_SIZE_POS
            + ArchieveDataDesc.MSG_SIZE_LEN
        ],
    )

    records_count = validate_int_field(
        field="record count",
        msg_slice=msg_body[
            ArchieveDataDesc.RECORDS_COUNT_POS : ArchieveDataDesc.RECORDS_COUNT_POS
            + ArchieveDataDesc.RECORDS_COUNT_LEN
        ],
    )

    # drop header
    msg_body = msg_body[ArchieveDataDesc.RECORDS_START_POS :]

    # check that msg_len equals real message len
    try:
        real_msg_len = len(msg_body)
        assert msg_len == real_msg_len
    except AssertionError:
        raise TooShortMessage(expected_len=msg_len, slice=msg_body)

    records: List[str] = []

    for i in range(records_count):
        record_len = validate_int_field(
            field=f"Record #{i} length",
            msg_slice=msg_body[: ArchieveDataDesc.SINGLE_RECORD_SIZE_LEN],
        )
        # drop len
        msg_body = msg_body[ArchieveDataDesc.SINGLE_RECORD_SIZE_LEN :]

        # extract record
        b_record = msg_body[:record_len]
        try:
            record = b_record.decode(ENCODING)
        except Exception:
            raise InvalidField("Archieve data record", b_record)
        records.append(record)

        msg_body = msg_body[record_len:]

    archieve_data = ArchieveData(product_id, msg_len, records_count, records)

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


def _handle_errors(method: Callable):
    @wraps
    def _impl(self: "PacketParser", *method_args, **method_kwargs):
        if not isinstance(self, PacketParser):
            raise ValueError(
                "This decorator does not support any classes but `PacketParser`!"
            )

        def handle_error(err: Exception, message: str):
            pass

        try:
            method_output = method(self, *method_args, **method_kwargs)
        except Exception:
            pass

    return _impl


class PacketParser:
    def __init__(self) -> None:
        self._packet_code: Optional[int] = None
        self._scanner_id: Optional[str] = None

        self._header: Optional[HeaderPacket] = None
        self._packet: ParsedPacketType = None

        self._formatted_raw_msg: str = ""

    @_handle_errors
    def get_parsed_message(self, msg: bytes) -> ParsedPacketType:
        self._header = self._parse_header(msg[0 : HeaderDesc.HEADER_LEN])

        self._packet_code = self._header.packet_code
        self._scanner_id = self._header.scanner_ID

        msg_body = msg[HeaderDesc.HEADER_LEN :]

        if self._header.packet_code == PacketCode.STATE_CONTROL_CODE:
            self._packet = parse_state_control_response_packet(msg_body)
        elif self._header.packet_code == PacketCode.SETTINGS_SET_CODE:
            self._packet = parse_settings_set_response_packet(msg_body)
        if self._header.packet_code == PacketCode.ARCHIEVE_DATA_CODE:
            self._packet = parse_archieve_data(msg_body)

        return self._packet

    def _parse_int_field(self, field_name: str, _slice: bytes) -> int:
        try:
            return int.from_bytes(_slice, byteorder=ProtocolDesc.BYTEORDER)
        except Exception:
            raise InvalidField(f"{field_name}", _slice)

    def _parse_header(self, msg_header: bytes) -> HeaderPacket:

        b_preambula = msg_header[HeaderDesc.PREAMBULA_POS : HeaderDesc.SCANNER_ID_POS]
        b_scanner_ID = msg_header[HeaderDesc.SCANNER_ID_POS : HeaderDesc.PACKET_ID_POS]
        b_packet_ID = msg_header[HeaderDesc.PACKET_ID_POS : HeaderDesc.PACKET_CODE_POS]
        b_packet_code = msg_header[HeaderDesc.PACKET_CODE_POS :]

        return HeaderPacket(
            preambula=self._validate_preambula(b_preambula),
            scanner_ID=self._validate_scanner_id(b_scanner_ID),
            packet_ID=self._validate_packet_id(b_packet_ID),
            packet_code=self._validate_packet_code(b_packet_code),
        )

    def _validate_preambula(self, _slice: bytes) -> str:
        try:
            preambula = _slice.decode(ProtocolDesc.ENCODING)
            assert preambula == ProtocolDesc.PREAMBULA
            return preambula
        except Exception:
            raise InvalidField(field="Preambula", slice=_slice)

    def _validate_scanner_id(self, _slice: bytes) -> str:
        try:
            return format_hex_bytes(_slice)
        except Exception:
            raise InvalidField(field="Scanner ID", slice=_slice)

    def _validate_packet_id(self, _slice: bytes) -> int:
        try:
            packet_id = self._parse_int_field(field_name="Packet ID", _slice=_slice)
            return packet_id
        except Exception:
            raise InvalidField(field="Packet ID", slice=_slice)

    def _validate_packet_code(self, _slice: bytes) -> PacketCode:
        try:
            packet_code = self._parse_int_field(field_name="Packet Code", _slice=_slice)
            assert PacketCode.has_value(packet_code) is True
            return packet_code  # type: ignore
        except Exception:
            raise InvalidField(field="Packet Code", slice=_slice)

    def _parse_state_control_response_packet(
        self, msg_body: bytes
    ) -> ScannerControlResponse:

        try:
            assert len(msg_body) == StateControlDesc.RESERVED_LEN
            reserved = self._parse_int_field(field_name="Reserved", _slice=msg_body)
            assert reserved == 0
        except Exception:
            raise InvalidField("Reserved", msg_body)

        return ScannerControlResponse(
            self._header.preambula,  # type: ignore
            self._header.scanner_ID,  # type: ignore
            self._header.packet_ID,  # type: ignore
            self._header.packet_code,  # type: ignore
            reserved,
        )

    # def get_packet_code(self, msg: bytes) -> int:
    #     if len(msg) < MIN_MSG_LEN:
    #         raise TooShortMessage(None, msg)

    #     header = is_valid_header(msg[0:HEADER_LEN])
    #     self._packet_code = header.packet_code
    #     return header.packet_code

    # def get_scanner_id(self, msg: bytes) -> str:
    #     if len(msg) < MIN_MSG_LEN:
    #         raise TooShortMessage(None, msg)

    #     header = is_valid_header(msg[0:HEADER_LEN])
    #     return header.scanner_ID
