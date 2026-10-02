import json
from collections import Counter

import pytest

from app.config import Settings
from app.fallback import ExampleBank
from app.textutil import URDU_FULL_STOP, URDU_QUESTION_MARK, count_letters
from app.tiles import TileBank
from evaluation.cases import DEFAULT_CASES, cases_digest, load_cases

SETTINGS = Settings()


@pytest.fixture(scope="module")
def cases():
    return load_cases()


def test_dataset_size_and_splits(cases):
    assert 100 <= len(cases) <= 150
    counts = Counter(c.split for c in cases)
    assert counts["urdu"] >= 60 and counts["code_mixed"] >= 30


def test_ids_are_unique_and_prefixed_by_split(cases):
    assert len({c.id for c in cases}) == len(cases)
    assert all(c.id.startswith("u" if c.split == "urdu" else "c") for c in cases)


def test_every_tile_exists(cases):
    bank = TileBank.load(SETTINGS.data_dir / "tiles.json")
    for case in cases:
        bank.resolve(case.tiles)


def test_each_selection_appears_once_per_speaker_gender(cases):
    keys = [(tuple(c.tiles), c.gender) for c in cases]
    assert len(set(keys)) == len(keys)


def test_no_case_reuses_a_few_shot_example_selection(cases):
    examples = ExampleBank.load(SETTINGS.data_dir / "examples.json")
    example_sets = {frozenset(e.tiles) for e in examples.examples}
    assert not [c.id for c in cases if frozenset(c.tiles) in example_sets]


def test_references_are_urdu_script_sentences(cases):
    for case in cases:
        assert case.english.strip()
        for ref in case.references:
            arabic, _ = count_letters(ref)
            assert arabic > 0, case.id
            assert ref == ref.strip(), case.id
            assert not ref.endswith((URDU_FULL_STOP, URDU_QUESTION_MARK, ".")), case.id


def test_monolingual_references_have_no_latin_letters(cases):
    for case in (c for c in cases if c.split == "urdu"):
        assert all(count_letters(ref)[1] == 0 for ref in case.references), case.id


def test_code_mixed_cases_have_a_latin_script_first_reference(cases):
    for case in (c for c in cases if c.split == "code_mixed"):
        assert count_letters(case.references[0])[1] > 0, case.id


def test_gendered_cases_exist_for_both_genders(cases):
    assert {c.gender for c in cases} >= {"male", "female"}


def test_loader_rejects_duplicate_ids(tmp_path):
    line = json.dumps(
        {"id": "x1", "split": "urdu", "tiles": ["person_i_me"], "references": ["a"], "english": "a"}
    )
    path = tmp_path / "cases.jsonl"
    path.write_text(line + "\n" + line + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_cases(path)


def test_digest_changes_with_content(tmp_path):
    path = tmp_path / "cases.jsonl"
    path.write_text("a", encoding="utf-8")
    first = cases_digest(path)
    path.write_text("b", encoding="utf-8")
    assert cases_digest(path) != first
    assert len(cases_digest(DEFAULT_CASES)) == 64
