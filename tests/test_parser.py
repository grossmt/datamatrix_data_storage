from dataclasses import dataclass
from enum import Enum
from dm_storager.protocol.packet_parser import PacketParser


class TestMessages(Enum):
    GOOD_STATE_CTRL_MESSAGE = bytes(
        b"""
            RFLABC
            \x00\x01
            \x00\x01
            \x37
            \x00\x00\x00\x00"""
    )
    GOOD_SETTINGS_SET_MESSAGE = bytes(
        b"""
            RFLABC
            \x00\x01
            \x00\x01
            \x13
            \x00\x00\x00\x00
        """
    )
    GOOD_ARCHIEVE_DATA_MESSAGE = bytes(
        b"""
            RFLABC
            \x00\x01
            \x00\x01
            \x45
            \x01
            \x00\x13
            \x02
            \x08
            \x01\x23\x45\x67\x89\x74\x87\x0D
            \x09
            \xAB\xCD\xEF\xBD\x34\x45\x73\x14\x0D
        """
    )

    BAD_HEADER_MESSAGE = bytes()


parser = PacketParser(debug=True)


def test_parse_good_ctrl_message():
    # given
    test_msg = TestMessages.GOOD_STATE_CTRL_MESSAGE
    # when
    parsed_packet = parser.get_parsed_message(test_msg)
    # then
    assert parsed_packet
