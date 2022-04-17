from dm_storager.exceptions import Error


class ProtocolMessageError(Error):
    """Base protocol exception"""

    def __init__(self, reason: str, msg: bytes) -> None:
        super().__init__(f"Input message error: {reason}: {msg}")


class TooShortMessage(ProtocolMessageError):
    def __init__(self, slice: bytes) -> None:
        super().__init__(reason="Too short message", msg=slice)

class InvalidField(ProtocolMessageError):
    def __init__(self, field: str, slice: bytes) -> None:
        super().__init__(reason=f"Invalid {field}", msg=slice)


