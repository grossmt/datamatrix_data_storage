from typing import Union

from dm_storager.const import STATE_CONTROL_CODE, SETTINGS_SET_CODE, ARCHIEVE_DATA_CODE

from dm_storager.schema import (
    ScannerControlResponse,
    SettingsSetResponse,
    ArchieveDataResponce,
)


def parse_input_message(
    msg: str,
) -> Union[ScannerControlResponse, SettingsSetResponse, ArchieveDataResponce, None]:

    packet = None

    if len(msg) < 14:
        return None
    
    preambula = msg[0:6]
    scanner_id = int(msg[6:8])
    packet_code = int(msg[10:11])
    packet_id = int(msg[8:10])

    if packet_code == STATE_CONTROL_CODE:
        packet = ScannerControlResponse(
            preambula=preambula,
            scanner_id=scanner_id,
            packet_code=packet_code,
            packet_id=packet_id,
        )

    if packet_code == SETTINGS_SET_CODE:
        response_code = int(msg[11:])
        packet = SettingsSetResponse(
            preambula=preambula,
            scanner_id=scanner_id,
            packet_code=packet_code,
            packet_id=packet_id,
            response_code=response_code,
        )

    if packet_code == ARCHIEVE_DATA_CODE:
        archieved_data = msg[11:]
        packet = ArchieveDataResponce(
            preambula=preambula,
            scanner_id=scanner_id,
            packet_code=packet_code,
            packet_id=packet_id,
            archieve_data=archieved_data,
        )

    return packet