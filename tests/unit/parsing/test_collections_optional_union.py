import pytest
from alloy.types import parse_output


pytestmark = pytest.mark.unit


def test_optional_and_union_basic():
    from typing import Optional, Union

    assert parse_output(Optional[str], "null") is None
    assert parse_output(Optional[str], '"x"') == "x"

    assert parse_output(Union[int, str], "7") == 7
    assert parse_output(Union[int, str], '"seven"') == "seven"


def test_list_of_union_values():
    from typing import Union

    raw = '[1, "2", 3, "four"]'
    out = parse_output(list[Union[int, str]], raw)
    assert out[0] == 1 and out[2] == 3 and out[3] == "four"
    assert out[1] in (2, "2")
