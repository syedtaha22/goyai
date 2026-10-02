from fastapi.testclient import TestClient

from app.config import Settings
from app.fallback import ExampleBank
from app.main import create_app
from app.textutil import URDU_FULL_STOP
from app.tiles import TileBank
from tests.fakes import FakeLLM


def make_http() -> TestClient:
    return TestClient(create_app(Settings(), FakeLLM()))


def test_every_example_references_known_tiles():
    settings = Settings()
    bank = TileBank.load(settings.data_dir / "tiles.json")
    examples = ExampleBank.load(settings.data_dir / "examples.json")
    assert len(examples) > 0
    for example in examples.examples:
        bank.resolve(example.tiles)


def test_suggest_matches_curated_example():
    with make_http() as http:
        body = http.post(
            "/v1/suggest", json={"tiles": ["person_i_me", "action_want", "food_water"]}
        ).json()
    assert body["source"] == "fallback"
    assert body["model"] is None
    assert body["candidates"][0] == {
        "urdu": "مجھے پانی چاہیے" + URDU_FULL_STOP,
        "english": "I want water.",
        "style": "urdu",
    }


def test_suggest_returns_n_candidates_and_code_mixed_style():
    with make_http() as http:
        three = http.post(
            "/v1/suggest", json={"tiles": ["person_i_me", "action_want", "food_donut"]}
        ).json()["candidates"]
        two = http.post(
            "/v1/suggest", json={"tiles": ["person_i_me", "action_want", "food_donut"], "n": 2}
        ).json()["candidates"]
        bathroom = http.post("/v1/suggest", json={"tiles": ["place_bathroom"]}).json()
    assert len(three) == 3 and len(two) == 2
    assert {c["style"] for c in bathroom["candidates"]} == {"urdu", "code_mixed"}


def test_exclude_is_honored():
    shown = "مجھے ڈونٹ چاہیے" + URDU_FULL_STOP
    with make_http() as http:
        cands = http.post(
            "/v1/suggest",
            json={
                "tiles": ["person_i_me", "action_want", "food_donut"],
                "exclude": [shown],
                "mode": "different",
            },
        ).json()["candidates"]
    assert shown not in [c["urdu"] for c in cands]
    assert len(cands) == 2


def test_no_candidate_mentions_a_different_item():
    with make_http() as http:
        cands = http.post(
            "/v1/suggest", json={"tiles": ["person_i_me", "action_want", "food_donut"], "n": 5}
        ).json()["candidates"]
    assert all("پانی" not in c["urdu"] for c in cands)


def test_unmatched_selection_reads_out_tile_labels():
    with make_http() as http:
        cands = http.post(
            "/v1/suggest", json={"tiles": ["food_cake", "place_park"]}
        ).json()["candidates"]
    assert len(cands) == 1
    assert cands[0]["urdu"] == "کیک پارک" + URDU_FULL_STOP
    assert cands[0]["english"] == "cake park."


def test_personalization_label_used_in_readout():
    with make_http() as http:
        cands = http.post(
            "/v1/suggest",
            json={
                "tiles": ["personalization_favorite_toy"],
                "profile": {
                    "custom_labels": {
                        "personalization_favorite_toy": {"urdu": "گڑیا", "english": "doll"}
                    }
                },
            },
        ).json()["candidates"]
    assert cands[0]["urdu"] == "گڑیا" + URDU_FULL_STOP


def test_unknown_tile_is_422():
    with make_http() as http:
        r = http.post("/v1/suggest", json={"tiles": ["person_i_me", "bogus"]})
    assert r.status_code == 422
    assert "bogus" in r.json()["detail"]


def test_custom_label_on_ordinary_tile_is_422():
    with make_http() as http:
        r = http.post(
            "/v1/suggest",
            json={
                "tiles": ["action_eat"],
                "profile": {"custom_labels": {"action_eat": {"urdu": "x", "english": "x"}}},
            },
        )
    assert r.status_code == 422


def test_request_limits_are_422():
    with make_http() as http:
        assert http.post("/v1/suggest", json={"tiles": []}).status_code == 422
        too_many = ["person_i_me"] * 7
        assert http.post("/v1/suggest", json={"tiles": too_many}).status_code == 422
        assert http.post("/v1/suggest", json={"tiles": ["person_i_me"], "n": 9}).status_code == 422


def test_tiles_endpoint_lists_bank():
    with make_http() as http:
        tiles = http.get("/v1/tiles").json()
    assert len(tiles) == 204
    assert {"tile_id", "category", "english", "urdu", "arasaac_id"} <= set(tiles[0])
