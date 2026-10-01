from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

from app.textutil import reject_hidden_characters

Style = Literal["urdu", "code_mixed"]
Gender = Literal["male", "female"]

# Whitespace is trimmed first, so whitespace-only text is rejected as empty.
LabelText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=60),
    AfterValidator(reject_hidden_characters),
]
ExcludedSentence = Annotated[str, StringConstraints(max_length=200)]


class Label(BaseModel):
    """
    A user-supplied display label for a personalization tile.
    """

    urdu: LabelText
    english: LabelText


class Profile(BaseModel):
    """
    Per-user settings from the personalization layer.

    Attributes:
        gender: Used to choose gendered Urdu verb forms. Left unset when unknown.
        custom_labels: Labels for personalization tiles, keyed by tile_id.
    """

    gender: Gender | None = None
    custom_labels: dict[str, Label] = Field(default_factory=dict, max_length=12)


class SuggestRequest(BaseModel):
    """
    Request for candidate sentences from an ordered tile selection.

    Attributes:
        tiles: Selected tile IDs in selection order.
        profile: Per-user settings.
        exclude: Urdu sentences already shown, which should not be returned again.
        n: Number of candidates wanted.
        mode: "different" asks for more varied candidates for the same tiles.
    """

    tiles: list[str] = Field(min_length=1, max_length=6)
    profile: Profile = Field(default_factory=Profile)
    exclude: list[ExcludedSentence] = Field(default_factory=list, max_length=20)
    n: int = Field(default=3, ge=1, le=5)
    mode: Literal["default", "different"] = "default"


class Candidate(BaseModel):
    """
    One suggested sentence.
    """

    urdu: str
    english: str
    style: Style


class SuggestResponse(BaseModel):
    """
    Ranked candidate sentences, best first.

    Attributes:
        source: "llm" when the language model produced the candidates, "fallback" otherwise.
        model: Model name when source is "llm", otherwise None.
        latency_ms: Time spent producing the candidates.
    """

    candidates: list[Candidate]
    source: Literal["llm", "fallback"]
    model: str | None = None
    latency_ms: int
