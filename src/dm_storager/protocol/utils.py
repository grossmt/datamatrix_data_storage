from dm_storager.protocol.const import (
    ENCODING,
    PACKET_CODE_LEN,
    SCANNER_ID_POS,
    PACKET_ID_POS,
    PACKET_CODE_POS,
)

SEPATATORS_POS = [
    SCANNER_ID_POS,
    PACKET_ID_POS,
    PACKET_CODE_POS,
    PACKET_CODE_POS + PACKET_CODE_LEN
]

def format_bytestring(msg: bytes) -> str:

    def insert_dash(string, index):
        assert index <= len(string)
        return string[:index] + ' ' + string[index:]

    s_msg = msg.decode(ENCODING)
    iteration = 0
    for i in SEPATATORS_POS:
        try:
            s_msg = insert_dash(s_msg, i + iteration)
            iteration += 1
        except AssertionError:
            return s_msg
    return s_msg
