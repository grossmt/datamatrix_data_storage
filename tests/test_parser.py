import pytest

from enum import Enum
from dm_storager.protocol.packet_parser import PacketParser


class TestMessages(Enum):
    GOOD_STATE_CTRL_MESSAGE = bytes(b"""RFLABC\x00\x01\x00\x01\x37\x00\x00\x00\x00""")
    GOOD_SETTINGS_SET_MESSAGE = bytes(b"""RFLABC\x00\x01\x00\x01\x13\x00\x00\x00\x00""")
    GOOD_ARCHIEVE_DATA_MESSAGE = bytes(
        b"""RFLABC\x00\x01\x00\x01\x45\x01\x00\x13\x02\x08\x01\x23\x45\x67\x97\x74\x87\x0D\x09\xAB\xCD\xEF\xBD\x34\x45\x73\x14\x0D"""
    )

    # General failure
    TOO_SHORT_MESSAGE = bytes(b"""RFLABC\x00\x01\x00\x01\x37\x00\x00\x00""")
    BAD_PREAMBULA_MESSAGE = bytes(b"""RFLABD\x00\x01\x00\x01\x37\x00\x00\x00\x00""")
    BAD_PACKET_CODE_MESSAGE = bytes(b"""RFLABC\x00\x01\x00\x01\x38\x00\x00\x00\x00""")

    # State control failure
    BAD_STATE_CTRL_MESSAGE = bytes(b"""RFLABC\x00\x01\x00\x01\x37\x00\x00\x00\x01""")

    # Settings set failure ???
    BAD_SETTINGS_SET_MESSAGE = bytes(b"""RFLABC\x00\x01\x00\x01\x13RFLA""")

    # Archieve data failure
    BAD_ARCHIEVE_DATA_PRODUCT_ID_MESSAGE = bytes(
        b"""RFLABC\x00\x01\x00\x01\x45\x08\x00\x13\x02\x08\x01\x23\x45\x67\x89\x74\x87\x0D\x09\xAB\xCD\xEF\xBD\x34\x45\x73\x14\x0D"""
    )
    BAD_ARCHIEVE_DATA_MESSAGE_SIZE_MESSAGE = bytes(
        b"""RFLABC\x00\x01\x00\x01\x45\x01\x00\x14\x02\x08\x01\x23\x45\x67\x89\x74\x87\x0D\x09\xAB\xCD\xEF\xBD\x34\x45\x73\x14\x0D"""
    )


parser = PacketParser(debug=True)


def test_parse_good_ctrl_message():
    # given
    test_msg = TestMessages.GOOD_STATE_CTRL_MESSAGE.value
    # when
    parsed_packet = parser.parse_message(test_msg)
    # then
    assert parsed_packet


def test_parse_good_settings_message():
    # given
    test_msg = TestMessages.GOOD_SETTINGS_SET_MESSAGE.value
    # when
    parsed_packet = parser.parse_message(test_msg)
    # then
    assert parsed_packet


def test_parse_good_archieve_data_message():
    # given
    test_msg = TestMessages.GOOD_ARCHIEVE_DATA_MESSAGE.value
    # when
    parsed_packet = parser.parse_message(test_msg)
    # then
    assert parsed_packet


def test_parse_too_short_message():
    # given
    test_msg = TestMessages.TOO_SHORT_MESSAGE.value
    # when
    parsed_packet = parser.parse_message(test_msg)
    # then
    assert parsed_packet is None


def test_parse_bad_preambula_message():
    # given
    test_msg = TestMessages.BAD_PREAMBULA_MESSAGE.value
    # when
    parsed_packet = parser.parse_message(test_msg)
    # then
    assert parsed_packet is None


def test_parse_bad_packet_code_message():
    # given
    test_msg = TestMessages.BAD_PACKET_CODE_MESSAGE.value
    # when
    parsed_packet = parser.parse_message(test_msg)
    # then
    assert parsed_packet is None


def test_parse_bad_state_control_message():
    # given
    test_msg = TestMessages.BAD_STATE_CTRL_MESSAGE.value
    # when
    parsed_packet = parser.parse_message(test_msg)
    # then
    assert parsed_packet is None


def test_parse_bad_settings_set_message():
    # given
    test_msg = TestMessages.BAD_SETTINGS_SET_MESSAGE.value
    # when
    parsed_packet = parser.parse_message(test_msg)
    # then
    assert parsed_packet


def test_parse_bad_archieve_data_product_id_message():
    # given
    test_msg = TestMessages.BAD_ARCHIEVE_DATA_PRODUCT_ID_MESSAGE.value
    # when
    parsed_packet = parser.parse_message(test_msg)
    # then
    assert parsed_packet is None


def test_parse_bad_arcieve_data_message_size_message():
    # given
    test_msg = TestMessages.BAD_ARCHIEVE_DATA_MESSAGE_SIZE_MESSAGE.value
    # when
    parsed_packet = parser.parse_message(test_msg)
    # then
    assert parsed_packet is None
