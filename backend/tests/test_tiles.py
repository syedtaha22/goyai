import re
from collections import Counter

import pytest

from app.config import Settings
from app.schemas import Label
from app.tiles import TileBank, UnknownTileError

URDU_CHARS = re.compile(r"^[؀-ۿݐ-ݿ\s]+$")

EXPECTED_COUNTS = {
    "person": 26,
    "action": 32,
    "place": 24,
    "feeling": 28,
    "body": 20,
    "food": 34,
    "social": 28,
    "personalization": 12,
}


@pytest.fixture(scope="module")
def bank() -> TileBank:
    return TileBank.load(Settings().data_dir / "tiles.json")


def test_bank_has_204_tiles_with_expected_category_sizes(bank):
    assert len(bank) == 204
    assert Counter(t.category for t in bank.tiles) == EXPECTED_COUNTS


def test_ids_are_unique_and_prefixed_by_category(bank):
    ids = [t.tile_id for t in bank.tiles]
    assert len(set(ids)) == len(ids)
    assert all(t.tile_id.startswith(t.category + "_") for t in bank.tiles)


def test_every_tile_has_urdu_script_label_and_english(bank):
    for t in bank.tiles:
        assert URDU_CHARS.match(t.urdu), t.tile_id
        assert t.english.strip(), t.tile_id


def test_resolve_keeps_order_and_repeats(bank):
    out = bank.resolve(["action_eat", "person_i_me", "action_eat"])
    assert [t.tile_id for t in out] == ["action_eat", "person_i_me", "action_eat"]


def test_resolve_unknown_tile(bank):
    with pytest.raises(UnknownTileError) as exc:
        bank.resolve(["person_i_me", "nope"])
    assert exc.value.tile_ids == ["nope"]


def test_custom_label_replaces_personalization_tile(bank):
    out = bank.resolve(
        ["personalization_childs_name"],
        {"personalization_childs_name": Label(urdu="علی", english="Ali")},
    )
    assert (out[0].urdu, out[0].english) == ("علی", "Ali")
    # The bank itself is not modified.
    assert bank.resolve(["personalization_childs_name"])[0].english == "child's name"


def test_custom_label_on_non_personalization_tile_rejected(bank):
    with pytest.raises(UnknownTileError):
        bank.resolve(["action_eat"], {"action_eat": Label(urdu="x", english="x")})
