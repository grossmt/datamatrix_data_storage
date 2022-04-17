from dm_storager.exceptions import Error


class ProtocolMessageError(Error):
    """Base protocol exception"""

    def __init__(self, reason: str, msg: bytes) -> None:
        super().__init__(f"Input message error: {reason}: {msg}")


class TooShortMessage(ProtocolMessageError):
    def __init__(self, slice: bytes) -> None:
        super().__init__(reason="Too short message", msg=slice)


class InvalidPreambula(ProtocolMessageError):
    def __init__(self, slice: bytes) -> None:
        super().__init__(reason="Invalid Preambula", msg=slice)


class InvalidScannerID(ProtocolMessageError):
    def __init__(self, slice: bytes) -> None:
        super().__init__(reason="Invalid Scanner ID", msg=slice)


class InvalidPacketCode(ProtocolMessageError):
    def __init__(self, slice: bytes) -> None:
        super().__init__(reason="Invalid Packet Code", msg=slice)


class InvalidPacketID(ProtocolMessageError):
    def __init__(self, slice: bytes) -> None:
        super().__init__(reason="Invalid Packet ID", msg=slice)
