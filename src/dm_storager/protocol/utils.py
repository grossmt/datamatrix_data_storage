import binascii

from dm_storager.protocol.const import (
    ENCODING,
    HEX_PADDING,
    PACKET_CODE_LEN,
    SCANNER_ID_POS,
    PACKET_ID_POS,
    PACKET_CODE_POS,
)

SEPATATORS_POS = [
    18,
    24,
    30,
    33,
]


def format_bytestring(msg: bytes) -> str:
    def insert_dash(string, index):
        assert index <= len(string)
        return string[: index - 1] + " | " + string[index:]

    s_msg = str(repr(binascii.hexlify(msg, "-"))[2:-1]).replace("\\x", "")
    iteration = 0
    for i in SEPATATORS_POS:
        try:
            s_msg = insert_dash(s_msg, i + iteration)
            iteration += 2
        except AssertionError:
            return s_msg
    return s_msg


def format_hex_bytes(slice: bytes) -> str:
    return f"0x{slice.hex()}".upper().replace("0X", "0x")
