from dataclasses import dataclass
from enum import IntEnum

ENCODING = "cp1251"
BYTEORDER = "big"

PREAMBULA = "RFLABC"

HEX_PADDING = 6


# HEADER
PREAMBULA_LEN = len(PREAMBULA)
SCANNER_ID_LEN = 2
PACKET_ID_LEN = 2
PACKET_CODE_LEN = 1

HEADER_LEN = PREAMBULA_LEN + SCANNER_ID_LEN + PACKET_ID_LEN + PACKET_CODE_LEN

# STATE CONROL
STATE_CONTROL_RESERVED_LEN = 4
STATE_CONTROL_PACKEN_LEN = HEADER_LEN + STATE_CONTROL_RESERVED_LEN

# SETTINGS REQUEST
PRODUCT_NAME_LEN = 32
PRODUCT_COUNT = 6
SERVER_IP_LEN = 4
SERVER_PORT_LEN = 2
GATEWAY_IP_LEN = 4
NETMASK_LEN = 4
SETTINGS_RESERVED_LEN = 50
SETTINGS_REQUEST_PACKET_LEN = (
    HEADER_LEN
    + PRODUCT_NAME_LEN * PRODUCT_COUNT
    + SERVER_IP_LEN
    + SERVER_PORT_LEN
    + GATEWAY_IP_LEN
    + NETMASK_LEN
    + SETTINGS_RESERVED_LEN
)

# SETTINGS RESPONSE
SETTINGS_APPLY_STATUS_LEN = 4
SETTINGS_RESPONSE_LEN = HEADER_LEN + SETTINGS_APPLY_STATUS_LEN

# ARCHIEVE DATA

RECORD_PRODUCT_ID_LEN = 1
RECORD_MSG_LEN = 2
RECORD_COUNT_LEN = 2
RECORD_SINGLE_LEN = 1


RECORD_COUNT_LEN = 1
RECORD_SINGLE_LEN = 2
RECORD_PRODUCT_ID_LEN = 1

RECORD_COUNT_POS = 0
RECORD_SINGLE_POS = RECORD_COUNT_POS + RECORD_COUNT_LEN
RECORD_PRODUCT_ID_POS = RECORD_SINGLE_POS + RECORD_SINGLE_LEN

RECORDS_START_POS = RECORD_COUNT_LEN + RECORD_SINGLE_LEN + RECORD_PRODUCT_ID_LEN

# ARCHIEVE DATA RESPONSE
ARCHIEVE_STATUS_LEN = 4
ARCHIEVE_RESPONSE_LEN = HEADER_LEN + ARCHIEVE_STATUS_LEN

# POSITIONS
PREAMBULA_POS = 0
SCANNER_ID_POS = PREAMBULA_POS + PREAMBULA_LEN
PACKET_ID_POS = SCANNER_ID_POS + SCANNER_ID_LEN
PACKET_CODE_POS = PACKET_ID_POS + PACKET_ID_LEN

MIN_MSG_LEN = min(
    STATE_CONTROL_PACKEN_LEN, SETTINGS_RESPONSE_LEN, ARCHIEVE_RESPONSE_LEN
)


@dataclass
class ProtocolDesc:
    PREAMBULA: str = "RFLABC"
    HEX_PADDING: int = 6
    ENCODING: str = "cp1251"
    BYTEORDER: str = "big"


class HeaderDesc(IntEnum):
    """
    Header Descriptors.

    """

    # size of fields
    PREAMBULA_LEN = len(ProtocolDesc.PREAMBULA)
    SCANNER_ID_LEN = 2
    PACKET_ID_LEN = 2
    PACKET_CODE_LEN = 1

    HEADER_LEN = 11
    # position of fields


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
    RECORDS_COUNT_LEN = 2
    SINGLE_RECORD_SIZE_LEN = 1
    # position of fields
    PRODUCT_CODE_POS = 0
    MGS_SIZE_POS = 1
    RECORDS_COUNT_POS = 3
    RECORDS_START_POS = 4


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
