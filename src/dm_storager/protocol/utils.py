import binascii
from typing import Optional, Union

from dm_storager.protocol.const import ProtocolDesc

# SEPATATORS_POS = [
#     18,
#     24,
#     30,
#     33,
# ]


# def format_bytestring(msg: bytes) -> str:
#     def insert_dash(string, index):
#         assert index <= len(string)
#         return string[: index - 1] + " | " + string[index:]

#     s_msg = str(repr(binascii.hexlify(msg, "-"))[2:-1]).replace("\\x", "")
#     iteration = 0
#     for i in SEPATATORS_POS:
#         try:
#             s_msg = insert_dash(s_msg, i + iteration)
#             iteration += 2
#         except AssertionError:
#             return s_msg
#     return s_msg


def format_hex_value(value: Union[bytes, str]) -> Optional[str]:
    """Convert bytes list or str to formatted HEX str.

    For example: \xab\cd  -> "0xABCD"
    For example: "0xabcd" -> "0xABCD"
    For example: "10"     -> "0x000A"
    For example: "abcd"   -> None

    Args:
        slice (bytes | str): source bytes or str to convert.

    Returns:
        str: converted string.

    """

    if isinstance(value, bytes):
        # return formatted bytes to str
        return f"0x{value.hex()}".upper().replace("0X", "0x")

    elif isinstance(value, str):

        def format_id(source_str: str, base: int) -> str:
            return f"{int(source_str, base):#0{ProtocolDesc.HEX_PADDING}x}".upper().replace(
                "0X", "0x"
            )

        # check for DEC or HEX
        try:
            value.index("0x")
            return format_id(value, 16)  # value is HEX
        except ValueError:
            try:
                return format_id(value, 10)  # value is DEC
            except ValueError:
                return None
    else:
        return None  # unreacheble situation
