import json
from pathlib import Path

from pydantic import BaseModel

from app.schemas import Candidate
from app.tiles import Tile

URDU_FULL_STOP = "\u06d4"

# Minimum overlap between the selected tiles and an example's tiles for the example to apply.
MIN_JACCARD = 0.5


class Example(BaseModel):
    """
    A curated tile selection with its reference candidate sentences.
    """

    tiles: list[str]
    candidates: list[Candidate]


class ExampleBank:
    """
    Curated examples used to answer without the language model.
    """

    def __init__(self, examples: list[Example]) -> None:
        self._examples = examples

    @classmethod
    def load(cls, path: Path) -> "ExampleBank":
        """
        Load examples from a JSON file containing a list of example records.
        """
        records = json.loads(path.read_text(encoding="utf-8"))
        return cls([Example(**r) for r in records])

    def __len__(self) -> int:
        return len(self._examples)

    def suggest(self, tiles: list[Tile], n: int, exclude: list[str]) -> list[Candidate]:
        """
        Build candidates without the language model.

        An example applies when one of the two tile sets contains the other and their Jaccard
        similarity is at least MIN_JACCARD, so an example never contributes a sentence about
        a tile the user did not select. Applicable examples contribute their candidates, best
        match first. When no example applies,
        the labels of the selected tiles are read out in order as a single candidate, so the
        user still sees their selection as text.

        Args:
            tiles: Selected tiles in selection order.
            n: Maximum number of candidates.
            exclude: Urdu sentences that should not be returned.

        Returns:
            At most n candidates, without repeats of each other or of the exclude list.
        """
        selected = {t.tile_id for t in tiles}
        scored = []
        for order, example in enumerate(self._examples):
            tile_set = set(example.tiles)
            if not (selected <= tile_set or tile_set <= selected):
                continue
            score = len(selected & tile_set) / len(selected | tile_set)
            if score >= MIN_JACCARD:
                scored.append((-score, order, example))
        scored.sort(key=lambda s: (s[0], s[1]))

        seen = set(exclude)
        out: list[Candidate] = []
        for _, _, example in scored:
            for cand in example.candidates:
                if cand.urdu not in seen:
                    seen.add(cand.urdu)
                    out.append(cand)
        if not out:
            readout = Candidate(
                urdu=" ".join(t.urdu for t in tiles) + URDU_FULL_STOP,
                english=" ".join(t.english for t in tiles) + ".",
                style="urdu",
            )
            if readout.urdu not in seen:
                out.append(readout)
        return out[:n]
