from dm_storager.protocol.const import (
    ENCODING,
    HEX_PADDING,
    PACKET_CODE_LEN,
    SCANNER_ID_POS,
    PACKET_ID_POS,
    PACKET_CODE_POS,
)

SEPATATORS_POS = [
    SCANNER_ID_POS,
    PACKET_ID_POS,
    PACKET_CODE_POS,
    PACKET_CODE_POS + PACKET_CODE_LEN,
]


def format_bytestring(msg: bytes) -> str:
    def insert_dash(string, index):
        assert index <= len(string)
        return string[:index] + " " + string[index:]

    s_msg = msg.decode(ENCODING)
    iteration = 0
    for i in SEPATATORS_POS:
        try:
            s_msg = insert_dash(s_msg, i + iteration)
            iteration += 1
        except AssertionError:
            return s_msg
    return s_msg


def format_hex_bytes(slice: bytes) -> str:
    return f"{slice.hex():#0{HEX_PADDING}x}".upper().replace("0X", "0x")
