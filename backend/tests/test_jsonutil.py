import pytest

from app.llm.jsonutil import extract_json_object


def test_plain_object():
    assert extract_json_object('{"a": 1}') == {"a": 1}


def test_markdown_fence_and_prose():
    text = 'Sure!\n```json\n{"urdu": "ہیلو"}\n```\n(Note: extra text)'
    assert extract_json_object(text) == {"urdu": "ہیلو"}


def test_first_object_wins():
    assert extract_json_object('{"a": 1} then {"b": 2}') == {"a": 1}


def test_skips_broken_prefix():
    assert extract_json_object('{oops {"a": [1, {"b": 2}]}') == {"a": [1, {"b": 2}]}


@pytest.mark.parametrize("text", ["", "no json here", "[1, 2, 3]", "{unterminated"])
def test_no_object_raises(text):
    with pytest.raises(ValueError):
        extract_json_object(text)
