import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas import Gender

DEFAULT_CASES = Path(__file__).resolve().parent / "cases.jsonl"


class EvalCase(BaseModel):
    """
    One evaluation case: a tile selection and the sentences a speaker may mean by it.

    Attributes:
        id: Unique case identifier.
        split: "urdu" for monolingual Urdu, "code_mixed" for Urdu with English words.
        tiles: Selected tile IDs in selection order.
        gender: Speaker gender passed in the profile, or None.
        references: Acceptable Urdu sentences, without final punctuation. For code-mixed cases
            the English words appear in Latin script and, as further references, in Urdu script.
        english: English gloss of the intended meaning.
    """

    id: str
    split: Literal["urdu", "code_mixed"]
    tiles: list[str] = Field(min_length=1, max_length=6)
    gender: Gender | None = None
    references: list[str] = Field(min_length=1)
    english: str


def load_cases(path: Path = DEFAULT_CASES) -> list[EvalCase]:
    """
    Read evaluation cases from a JSON Lines file.

    Args:
        path: The cases file.

    Raises:
        ValueError: If two cases share an id.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    cases = [EvalCase(**json.loads(line)) for line in lines if line.strip()]
    ids = [c.id for c in cases]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate case id")
    return cases


def cases_digest(path: Path = DEFAULT_CASES) -> str:
    """
    SHA-256 of the cases file, recorded with each run to identify the dataset version.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()
