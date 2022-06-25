import binascii

from functools import wraps
from typing import Callable, List, Union, Optional

from dm_storager.protocol.exceptions import (
    InvalidField,
    TooShortMessage,
)
from dm_storager.protocol.const import (
    ProtocolDesc,
    HeaderDesc,
    StateControlDesc,
    ScannerSettingsDesc,
    ArchieveDataDesc,
    PacketCode,
    MIN_MSG_LEN,
)

from dm_storager.protocol.schema import (
    ArchieveData,
    HeaderPacket,
    ScannerControlResponse,
    SettingsSetResponse,
    ArchieveDataRequest,
)
from dm_storager.protocol.utils import format_hex_value
from dm_storager.utils.logger import configure_logger

ParsedPacketType = Union[
    ScannerControlResponse, SettingsSetResponse, ArchieveDataRequest, None
]


def _handle_errors(method: Callable):
    @wraps
    def _impl(self: "PacketParser", *method_args, **method_kwargs):
        def handle_error(err: Exception):
            self._logger.error(err)
            self._logger.error(f"Parsed message: \n{self._formatted_raw_msg}")

            formatted_raw_msg = self._format_byte_string(
                "Unparsed message", self._msg[self._fail_index_start :]
            )
            self._logger.error(f"{formatted_raw_msg}")

        try:
            method_output = method(self, *method_args, **method_kwargs)
            self._logger.debug(f"Parsed message: \n{self._formatted_raw_msg}")
            return method_output
        except (TooShortMessage, InvalidField) as err:
            handle_error(err)
            return None

    return _impl


class PacketParser:
    def __init__(self, debug: bool = False) -> None:
        self._packet_code: Optional[int] = None
        self._scanner_id: Optional[str] = None

        self._header: Optional[HeaderPacket] = None
        self._packet: ParsedPacketType = None
        self._fail_index_start: int = 0

        self._formatted_raw_msg: str = ""

        self._logger = configure_logger("PROTOCOL PARSER", debug)

    @_handle_errors
    def get_parsed_message(self, msg: bytes) -> ParsedPacketType:
        """Parse input message.

        Additionally format input bytes into human-readable format.

        Args:
            msg (bytes): raw input message from socket

        Returns:
            ParsedPacketType: parsed packet or None
        """

        self._formatted_raw_msg = ""
        self._packet = None
        self._packet_code = None
        self._scanner_id = None
        self._msg = msg

        if len(msg) < MIN_MSG_LEN:
            raise TooShortMessage(None, _slice=msg)

        self._header = self._parse_header(msg[: HeaderDesc.HEADER_LEN])

        self._packet_code = self._header.packet_code
        self._scanner_id = self._header.scanner_ID

        msg_body = msg[HeaderDesc.HEADER_LEN :]

        if self._header.packet_code == PacketCode.STATE_CONTROL_CODE:
            self._packet = self._parse_state_control_response_packet(msg_body)
        elif self._header.packet_code == PacketCode.SETTINGS_SET_CODE:
            self._packet = self._parse_settings_set_response_packet(msg_body)
        if self._header.packet_code == PacketCode.ARCHIEVE_DATA_CODE:
            self._packet = self._parse_archieve_data(msg_body)

        self._logger.debug(f"Formatted raw message: \n{self._formatted_raw_msg}")
        return self._packet

    def _parse_int_field(self, _slice: bytes) -> int:
        return int.from_bytes(_slice, byteorder=ProtocolDesc.BYTEORDER)

    def _format_byte_string(self, field_name: str, byte_str: bytes) -> str:
        s_msg = str(repr(binascii.hexlify(byte_str, "-"))[2:-1]).replace("\\x", "")

        return f"{field_name}: {s_msg}\n"

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
            self._formatted_raw_msg += self._format_byte_string("HEADER", _slice)

            preambula = _slice.decode(ProtocolDesc.ENCODING)
            assert preambula == ProtocolDesc.PREAMBULA
            return preambula
        except Exception:
            self._fail_index_start = HeaderDesc.PREAMBULA_POS
            raise InvalidField(field="Preambula", slice=_slice)

    def _validate_scanner_id(self, _slice: bytes) -> str:
        try:
            self._formatted_raw_msg += self._format_byte_string("SCANNER ID", _slice)
            return format_hex_value(_slice)  # type: ignore
        except Exception:
            self._fail_index_start = HeaderDesc.SCANNER_ID_POS
            raise InvalidField(field="Scanner ID", slice=_slice)

    def _validate_packet_id(self, _slice: bytes) -> int:
        try:
            self._formatted_raw_msg += self._format_byte_string("PACKET ID", _slice)
            return self._parse_int_field(_slice)
        except Exception:
            self._fail_index_start = HeaderDesc.PACKET_ID_POS
            raise InvalidField(field="Packet ID", slice=_slice)

    def _validate_packet_code(self, _slice: bytes) -> PacketCode:
        try:
            self._formatted_raw_msg += self._format_byte_string("PACKET CODE", _slice)

            packet_code = self._parse_int_field(_slice)
            assert PacketCode.has_value(packet_code) is True
            return packet_code  # type: ignore
        except Exception:
            self._fail_index_start = HeaderDesc.PACKET_CODE_POS
            raise InvalidField(field="Packet Code", slice=_slice)

    def _parse_state_control_response_packet(
        self, msg_body: bytes
    ) -> ScannerControlResponse:

        try:
            self._formatted_raw_msg += self._format_byte_string("RESERVED", msg_body)

            reserved = self._parse_int_field(msg_body)
            assert len(msg_body) == StateControlDesc.RESERVED_LEN
            assert reserved == 0
        except Exception:
            self._fail_index_start = StateControlDesc.RESERVED_POS
            raise InvalidField("Reserved", msg_body)

        return ScannerControlResponse(
            self._header.preambula,  # type: ignore
            self._header.scanner_ID,  # type: ignore
            self._header.packet_ID,  # type: ignore
            self._header.packet_code,  # type: ignore
            reserved,
        )

    def _parse_settings_set_response_packet(
        self, msg_body: bytes
    ) -> SettingsSetResponse:
        try:
            assert len(msg_body) == ScannerSettingsDesc.RESPONSE_CODE_LEN
            response_code = self._parse_int_field(msg_body)
        except Exception:
            self._fail_index_start = ScannerSettingsDesc.RESPONSE_CODE_POS
            raise InvalidField("Settings set response code", msg_body)

        return SettingsSetResponse(
            self._header.preambula,  # type: ignore
            self._header.scanner_ID,  # type: ignore
            self._header.packet_ID,  # type: ignore
            self._header.packet_code,  # type: ignore
            response_code,
        )

    def _parse_archieve_data(self, msg_body: bytes) -> ArchieveDataRequest:

        try:
            product_id = self._parse_int_field(
                _slice=msg_body[
                    ArchieveDataDesc.PRODUCT_CODE_POS : ArchieveDataDesc.PRODUCT_CODE_POS  # noqa:E501
                    + ArchieveDataDesc.PRODUCT_CODE_LEN
                ],
            )
            assert product_id < ScannerSettingsDesc.PRODUCT_COUNT
        except Exception:
            self._fail_index_start = (
                HeaderDesc.HEADER_LEN + ArchieveDataDesc.PRODUCT_CODE_POS
            )
            raise InvalidField("Archieve Data Product ID", msg_body)

        try:
            msg_len = self._parse_int_field(
                _slice=msg_body[
                    ArchieveDataDesc.MGS_SIZE_POS : ArchieveDataDesc.MGS_SIZE_POS
                    + ArchieveDataDesc.MSG_SIZE_LEN
                ],
            )
        except Exception:
            self._fail_index_start = (
                HeaderDesc.HEADER_LEN + ArchieveDataDesc.MGS_SIZE_POS
            )
            raise InvalidField("Archieve Data Message Size", msg_body)

        try:
            records_count = self._parse_int_field(
                _slice=msg_body[
                    ArchieveDataDesc.RECORDS_COUNT_POS : ArchieveDataDesc.RECORDS_COUNT_POS  # noqa:E501
                    + ArchieveDataDesc.RECORDS_COUNT_LEN
                ],
            )
        except Exception:
            self._fail_index_start = (
                HeaderDesc.HEADER_LEN + ArchieveDataDesc.RECORDS_COUNT_POS
            )
            raise InvalidField("Archieve Data Records Count", msg_body)

        # drop post-header consts
        msg_body = msg_body[ArchieveDataDesc.RECORDS_START_POS :]

        # check that msg_len equals real message len
        try:
            assert msg_len == len(msg_body)
        except AssertionError:
            self._fail_index_start = (
                HeaderDesc.HEADER_LEN + ArchieveDataDesc.RECORDS_START_POS
            )
            raise TooShortMessage(expected_len=msg_len, _slice=msg_body)

        records: List[str] = []

        for i in range(records_count):

            try:
                record_len = self._parse_int_field(
                    # field_name=f"Record #{i} length",
                    _slice=msg_body[: ArchieveDataDesc.SINGLE_RECORD_SIZE_LEN],
                )
                assert record_len > 0
            except Exception:
                self._fail_index_start = (
                    HeaderDesc.HEADER_LEN + ArchieveDataDesc.RECORDS_COUNT_POS
                )
                raise InvalidField(
                    f"Record #{i} length",
                    msg_body[: ArchieveDataDesc.SINGLE_RECORD_SIZE_LEN],
                )

            # drop len
            msg_body = msg_body[ArchieveDataDesc.SINGLE_RECORD_SIZE_LEN :]

            # extract record
            b_record = msg_body[:record_len]
            try:
                record = b_record.decode(ProtocolDesc.ENCODING)
            except Exception:
                raise InvalidField("Archieve data record", b_record)
            records.append(record)

            msg_body = msg_body[record_len:]

        archieve_data = ArchieveData(product_id, msg_len, records_count, records)

        return ArchieveDataRequest(
            self._header.preambula,  # type: ignore
            self._header.scanner_ID,  # type: ignore
            self._header.packet_ID,  # type: ignore
            self._header.packet_code,  # type: ignore
            archieve_data,
        )
