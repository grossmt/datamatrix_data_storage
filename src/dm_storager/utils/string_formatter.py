from typing import Optional

PADDING = 6


def format_id(source_str: str, base: int) -> str:
    return f"{int(source_str, base):#0{PADDING}x}".upper().replace("0X", "0x")


def hexify_id(given_id: str) -> Optional[str]:
    try:
        str(given_id).index("0x")
        return format_id(given_id, 16)
    except ValueError:
        try:
            return format_id(given_id, 10)
        except ValueError:
            return None
