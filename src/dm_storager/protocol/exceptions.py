from typing import Optional
from dm_storager.exceptions import Error


class ProtocolMessageError(Error):
    """Base protocol exception."""

    def __init__(self, reason: str, msg: bytes) -> None:
        super().__init__(f"Input message error: {reason}: {msg}")


class TooShortMessage(ProtocolMessageError):
    def __init__(self, expected_len: Optional[int], _slice: bytes) -> None:
        if expected_len:
            super().__init__(
                reason=f"Too short message (expected len = {expected_len}, given len = {len(_slice)})",
                msg=_slice,
            )
        else:
            super().__init__(reason="Too short message", msg=_slice)


class InvalidField(ProtocolMessageError):
    def __init__(self, field: str, slice: bytes) -> None:
        super().__init__(reason=f"Invalid {field}", msg=slice)
