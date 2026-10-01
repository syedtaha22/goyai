import json

import pytest

from app.config import Settings
from app.fallback import ExampleBank
from app.prompt import (
    PromptTemplates,
    build_messages,
    candidates_schema,
    render,
    render_tiles,
    select_examples,
)
from app.schemas import Label
from app.tiles import TileBank

SETTINGS = Settings()


@pytest.fixture(scope="module")
def bank() -> TileBank:
    return TileBank.load(SETTINGS.data_dir / "tiles.json")


@pytest.fixture(scope="module")
def examples() -> ExampleBank:
    return ExampleBank.load(SETTINGS.data_dir / "examples.json")


@pytest.fixture(scope="module")
def templates() -> PromptTemplates:
    return PromptTemplates.load(SETTINGS.data_dir / "prompts")


def build(bank, ids, templates, **kw):
    args = {"n": 3, "gender": None, "exclude": [], "shots": []}
    args.update(kw)
    return build_messages(templates, bank.resolve(ids), **args)


def test_schema_limits_candidates_to_n():
    schema = candidates_schema(4)
    assert schema["properties"]["candidates"]["maxItems"] == 4
    item = schema["properties"]["candidates"]["items"]
    assert item["required"] == ["urdu", "english", "style"]
    assert item["properties"]["style"]["enum"] == ["urdu", "code_mixed"]


def test_tiles_rendered_in_order_with_both_languages(bank):
    text = render_tiles(bank.resolve(["food_water", "person_i_me"]))
    lines = text.splitlines()
    assert lines[0].startswith("1. water (پانی)")
    assert lines[1].startswith("2. I/me (میں)")


def test_message_layout_without_shots(bank, templates):
    messages = build(bank, ["person_i_me", "action_want", "food_water"], templates)
    assert [m["role"] for m in messages] == ["system", "user"]
    assert "1. I/me" in messages[1]["content"] and "3. water" in messages[1]["content"]
    assert "up to 3 sentences" in messages[1]["content"]


@pytest.mark.parametrize(
    ("gender", "expected"),
    [("male", "masculine"), ("female", "feminine"), (None, "not known")],
)
def test_gender_rule_in_system_prompt(bank, templates, gender, expected):
    system = build(bank, ["person_i_me"], templates, gender=gender)[0]["content"]
    assert "{{" not in system
    assert expected in system


def test_exclude_only_appears_when_given(bank, templates):
    plain = build(bank, ["person_i_me"], templates)[-1]["content"]
    assert "already shown" not in plain
    shown = build(bank, ["person_i_me"], templates, exclude=["مجھے پانی چاہیے"])[-1]["content"]
    assert "already shown" in shown and "مجھے پانی چاہیے" in shown


def test_custom_label_reaches_prompt(bank, templates):
    tiles = bank.resolve(
        ["personalization_childs_name"],
        {"personalization_childs_name": Label(urdu="علی", english="Ali")},
    )
    messages = build_messages(templates, tiles, n=3, gender=None, exclude=[], shots=[])
    assert "Ali (علی)" in messages[-1]["content"]


def test_shots_become_user_assistant_pairs(bank, examples, templates):
    shots = [(bank.resolve(e.tiles), e) for e in examples.examples[:2]]
    messages = build(bank, ["person_i_me"], templates, shots=shots)
    roles = [m["role"] for m in messages]
    assert roles == ["system", "user", "assistant", "user", "assistant", "user"]
    answer = json.loads(messages[2]["content"])
    assert answer["candidates"][0]["urdu"] == examples.examples[0].candidates[0].urdu
    assert set(answer["candidates"][0]) == {"urdu", "english", "style"}


def test_select_examples_prefers_overlap_and_keeps_bank_order_on_ties(examples):
    picked = select_examples(examples.examples, {"person_i_me", "action_want", "food_donut"}, 2)
    assert set(picked[0].tiles) == {"person_i_me", "action_want", "food_donut"}
    assert len(picked) == 2


def test_select_examples_returns_at_most_k(examples):
    assert len(select_examples(examples.examples, {"x"}, 3)) == 3
    assert len(select_examples(examples.examples, {"x"}, 99)) == len(examples)


def test_render_fills_placeholders():
    assert render("a {{X}} b {{Y}}", X="1", Y="2") == "a 1 b 2"


def test_render_does_not_refill_substituted_text():
    assert render("{{A}} {{B}}", A="{{B}}", B="b") == "{{B}} b"


def test_render_missing_value_raises():
    with pytest.raises(KeyError):
        render("{{A}} {{B}}", A="a")


def test_shipped_templates_have_required_placeholders(templates):
    assert "{{GENDER_RULE}}" in templates.system
    assert "{{TILES}}" in templates.user_turn and "{{N}}" in templates.user_turn
    assert "{{SHOWN}}" in templates.already_shown


def write_templates(folder, **overrides):
    files = {
        "system.md": "rules {{GENDER_RULE}}",
        "user_turn.md": "{{TILES}} {{N}}",
        "already_shown.md": "{{SHOWN}}",
    }
    files.update(overrides)
    for name, text in files.items():
        (folder / name).write_text(text, encoding="utf-8")


def test_templates_load_from_folder_and_strip_whitespace(tmp_path):
    write_templates(tmp_path, **{"system.md": "\n rules {{GENDER_RULE}} \n\n"})
    assert PromptTemplates.load(tmp_path).system == "rules {{GENDER_RULE}}"


@pytest.mark.parametrize(
    "bad",
    [
        {"system.md": "no placeholder"},
        {"system.md": "{{GENDER_RULE}} {{EXTRA}}"},
        {"user_turn.md": "{{TILES}}"},
        {"already_shown.md": "{{SHOWN}} {{TILES}}"},
    ],
)
def test_templates_with_wrong_placeholders_are_rejected(tmp_path, bad):
    write_templates(tmp_path, **bad)
    with pytest.raises(ValueError):
        PromptTemplates.load(tmp_path)


def test_missing_template_file_is_an_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        PromptTemplates.load(tmp_path)
