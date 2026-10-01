import pytest

from app.postprocess import MAX_URDU_CHARS, clean_candidates
from app.textutil import URDU_FULL_STOP, URDU_QUESTION_MARK

WATER = "مجھے پانی چاہیے"
HOME = "مجھے گھر جانا ہے"


def item(urdu: str, english: str, style: str = "urdu") -> dict:
    return {"urdu": urdu, "english": english, "style": style}


def clean(items: list, n: int = 3, exclude: list[str] | None = None):
    return clean_candidates({"candidates": items}, n, exclude or [])


def test_accepts_clean_candidates_in_order():
    out = clean([item(WATER + URDU_FULL_STOP, "I want water."), item(HOME, "I want to go home")])
    assert [c.urdu for c in out] == [WATER + URDU_FULL_STOP, HOME + URDU_FULL_STOP]
    assert [c.english for c in out] == ["I want water.", "I want to go home."]


def test_ascii_punctuation_is_normalized():
    out = clean([item(WATER + ".", "x."), item("امی کہاں ہیں?", "Where is Mom?")])
    assert out[0].urdu == WATER + URDU_FULL_STOP
    assert out[1].urdu == "امی کہاں ہیں" + URDU_QUESTION_MARK


@pytest.mark.parametrize(
    "bad_urdu",
    [
        WATER + " (Note: this is a distractor)",
        "[" + WATER + "]",
        "Note: " + WATER,
        "*" + WATER + "*",
        "I want water",
        "",
        "   ",
        URDU_FULL_STOP,
        WATER + "\n" + HOME,
        "‮" + WATER,
        "مجھے​پانی",
        "ا" * (MAX_URDU_CHARS + 1),
    ],
)
def test_rejects_bad_urdu(bad_urdu):
    assert clean([item(bad_urdu, "I want water.")]) == []


@pytest.mark.parametrize("bad_english", ["", "مجھے پانی چاہیے", "I want (water)", "123", "x" * 161])
def test_rejects_bad_english(bad_english):
    assert clean([item(WATER, bad_english)]) == []


def test_zero_width_non_joiner_is_kept():
    out = clean([item("وہ آئیں‌گے", "They will come.")])
    assert len(out) == 1 and "‌" in out[0].urdu


def test_latin_words_make_a_candidate_code_mixed():
    out = clean([item("مجھے washroom جانا ہے", "I need the bathroom.", "urdu")])
    assert out[0].style == "code_mixed"


def test_model_style_kept_without_latin_letters():
    out = clean([item("مجھے واش روم جانا ہے", "I need the bathroom.", "code_mixed")])
    assert out[0].style == "code_mixed"


def test_unknown_style_defaults_to_urdu():
    out = clean([item(WATER, "I want water.", "slang")])
    assert out[0].style == "urdu"


def test_mostly_latin_text_is_rejected():
    assert clean([item("I want پانی please now", "I want water.")]) == []


def test_duplicates_removed_ignoring_punctuation_and_case():
    out = clean(
        [
            item(WATER + URDU_FULL_STOP, "I want water."),
            item(WATER, "I want water"),
            item(HOME, "I WANT WATER."),
        ]
    )
    assert len(out) == 1


def test_same_meaning_in_urdu_and_code_mixed_both_kept():
    out = clean(
        [
            item("مجھے واش روم جانا ہے", "I need the bathroom."),
            item("مجھے washroom جانا ہے", "I need the bathroom."),
        ]
    )
    assert [c.style for c in out] == ["urdu", "code_mixed"]


def test_exclude_list_is_honored_ignoring_punctuation():
    out = clean(
        [item(WATER, "I want water."), item(HOME, "I want to go home.")],
        exclude=[WATER + URDU_FULL_STOP],
    )
    assert [c.english for c in out] == ["I want to go home."]


def test_truncates_to_n():
    drinks = [("پانی", "water"), ("دودھ", "milk"), ("چائے", "tea")]
    items = [item(f"مجھے {w} چاہیے", f"I want {e}.") for w, e in drinks]
    assert len(clean(items, n=2)) == 2


def test_bad_items_do_not_discard_good_ones():
    out = clean(["junk", 5, None, {"urdu": WATER}, {"english": "x"}, item(WATER, "I want water.")])
    assert len(out) == 1


@pytest.mark.parametrize("raw", [{}, {"candidates": None}, {"candidates": "x"}, {"candidates": {}}])
def test_malformed_response_gives_no_candidates(raw):
    assert clean_candidates(raw, 3, []) == []
