import pytest

from alloy.types import parse_output

pytestmark = pytest.mark.unit


def test_parse_primitive_numbers_and_bool():
    assert parse_output(int, "123") == 123
    assert parse_output(float, "3.14") == 3.14
    assert parse_output(bool, "true") is True
    assert parse_output(bool, "False") is False


def test_parse_string_from_json_scalar_and_plain():
    assert parse_output(str, '"hello"') == "hello"
    assert parse_output(str, "hello") == "hello"
