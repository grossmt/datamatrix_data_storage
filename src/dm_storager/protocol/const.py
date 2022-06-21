from dataclasses import dataclass
from enum import IntEnum


class PacketCode(IntEnum):
    ERROR_CODE = 0x00
    STATE_CONTROL_CODE = 0x37
    SETTINGS_SET_CODE = 0x13
    ARCHIEVE_DATA_CODE = 0x45

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


class ResponseCode(IntEnum):
    SUCCSESS = 0
    ERROR = 1


@dataclass
class ProtocolDesc:
    PREAMBULA: str = "RFLABC"
    HEX_PADDING: int = 6
    ENCODING: str = "cp1251"
    BYTEORDER = "big"


class HeaderDesc(IntEnum):
    """
    Header Descriptors.

    """

    # size of fields
    PREAMBULA_LEN = len(ProtocolDesc.PREAMBULA)
    SCANNER_ID_LEN = 2
    PACKET_ID_LEN = 2
    PACKET_CODE_LEN = 1

    HEADER_LEN = PREAMBULA_LEN + SCANNER_ID_LEN + PACKET_ID_LEN + PACKET_CODE_LEN

    # position of fields
    PREAMBULA_POS = 0
    SCANNER_ID_POS = PREAMBULA_POS + PREAMBULA_LEN
    PACKET_ID_POS = SCANNER_ID_POS + SCANNER_ID_LEN
    PACKET_CODE_POS = PACKET_ID_POS + PACKET_ID_LEN


class StateControlDesc(IntEnum):
    # size of fields
    RESERVED_LEN = 4
    PACKET_LEN = HeaderDesc.HEADER_LEN + RESERVED_LEN


class ScannerSettingsDesc(IntEnum):
    # size of fields
    PRODUCT_NAME_LEN = 32
    PRODUCT_COUNT = 6
    SERVER_IP_LEN = 4
    SERVER_PORT_LEN = 2
    GATEWAY_IP_LEN = 4
    NETMASK_LEN = 4
    RESERVED_LEN = 50

    REQUEST_PACKET_LEN = (
        HeaderDesc.HEADER_LEN
        + PRODUCT_NAME_LEN * PRODUCT_COUNT
        + SERVER_IP_LEN
        + SERVER_PORT_LEN
        + GATEWAY_IP_LEN
        + NETMASK_LEN
        + RESERVED_LEN
    )

    RESPONSE_CODE_LEN = 4
    RESPONSE_PACKET_LEN = HeaderDesc.HEADER_LEN + RESPONSE_CODE_LEN


class ArchieveDataDesc(IntEnum):
    """
    Archieve Data Descriptors

    0: 0x01      - Product Code
    1: 0x00 0x13 - Messsage Length
    3: 0x02      - Records count
    4: 0x08      - Length of first record
       0x01 0x23 0x45 0x67 0x89 0xAB 0xCD 0x0D
       0x09      - Length of second record
       0xFE 0xDC 0xBA 0x98 0x76 0x54 0x32 0x10 0x0D
    """

    # size of fields
    PRODUCT_CODE_LEN = 1
    MSG_SIZE_LEN = 2
    RECORDS_COUNT_LEN = 1
    SINGLE_RECORD_SIZE_LEN = 1
    # position of fields
    PRODUCT_CODE_POS = 0
    MGS_SIZE_POS = 1
    RECORDS_COUNT_POS = 3
    RECORDS_START_POS = 4

    RESPONSE_CODE_LEN = 4
    RESPONSE_LEN = HeaderDesc.HEADER_LEN + RESPONSE_CODE_LEN


MIN_MSG_LEN = min(
    StateControlDesc.PACKET_LEN,
    ScannerSettingsDesc.RESPONSE_PACKET_LEN,
    ArchieveDataDesc.RESPONSE_LEN,
)
