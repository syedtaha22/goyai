import pytest
from pydantic import ValidationError

from app.schemas import Label, SuggestRequest
from tests.test_suggest import make_http

PERSONALIZATION = "personalization_childs_name"


def label_request(urdu: str, english: str = "Ali") -> dict:
    return {
        "tiles": [PERSONALIZATION],
        "profile": {"custom_labels": {PERSONALIZATION: {"urdu": urdu, "english": english}}},
    }


def test_label_is_trimmed():
    assert Label(urdu="  علی  ", english=" Ali ").urdu == "علی"


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "   ",
        "\t",
        "x\ny",
        "x\ty",
        "\u202eعلی\u202c",
        "\u200fعلی",
        "\u200eAli",
        "\u2067علی\u2069",
        "ع\u200bلی",
        "\ufeffعلی",
        "ا" * 61,
    ],
)
def test_label_rejects_bad_text(bad):
    with pytest.raises(ValidationError):
        Label(urdu=bad, english="Ali")
    with pytest.raises(ValidationError):
        Label(urdu="علی", english=bad)


def test_label_allows_zero_width_non_joiner():
    assert Label(urdu="ہوں\u200cگے", english="x").urdu == "ہوں\u200cگے"


def test_label_allows_latin_and_boundary_length():
    assert Label(urdu="Ali", english="Ali").urdu == "Ali"
    assert len(Label(urdu="ا" * 60, english="x").urdu) == 60


def test_exclude_item_length_is_capped():
    SuggestRequest(tiles=["person_i_me"], exclude=["ا" * 200])
    with pytest.raises(ValidationError):
        SuggestRequest(tiles=["person_i_me"], exclude=["ا" * 201])


@pytest.mark.parametrize("bad", ["   ", "x\ny", "\u202eعلی\u202c"])
def test_api_rejects_bad_label(bad):
    with make_http() as http:
        assert http.post("/v1/suggest", json=label_request(bad)).status_code == 422


def test_api_rejects_oversized_exclude_string():
    with make_http() as http:
        r = http.post("/v1/suggest", json={"tiles": ["person_i_me"], "exclude": ["ا" * 200_000]})
    assert r.status_code == 422


def test_api_uses_trimmed_label():
    with make_http() as http:
        r = http.post("/v1/suggest", json=label_request("  علی  "))
    assert r.status_code == 200
    assert r.json()["candidates"][0]["urdu"].startswith("علی")
