import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.fallback import Example
from app.schemas import Gender
from app.tiles import Tile

FEW_SHOT_COUNT = 4

_GENDER_RULES: dict[Gender | None, str] = {
    "male": "The speaker is male. Use masculine verb forms, for example چاہتا ہوں.",
    "female": "The speaker is female. Use feminine verb forms, for example چاہتی ہوں.",
    None: (
        "The speaker's gender is not known. Avoid verb forms that depend on it. For example, "
        "prefer مجھے پانی چاہیے over میں پانی چاہتا ہوں."
    ),
}

_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")

# Prompt file for each template, with the placeholders the file must contain.
_TEMPLATE_FILES = {
    "system": ("system.md", {"GENDER_RULE"}),
    "user_turn": ("user_turn.md", {"TILES", "N"}),
    "already_shown": ("already_shown.md", {"SHOWN"}),
}


def render(template: str, **values: str) -> str:
    """
    Fill the {{NAME}} placeholders of a template.

    Substitution happens in one pass, so a value that itself contains {{NAME}} is inserted
    as text and not filled in again.

    Args:
        template: Template text.
        **values: Replacement text keyed by placeholder name.

    Raises:
        KeyError: If the template has a placeholder without a value.
    """
    return _PLACEHOLDER.sub(lambda m: values[m.group(1)], template)


@dataclass(frozen=True)
class PromptTemplates:
    """
    The prompt texts, read from the markdown files in the prompts folder.

    Attributes:
        system: System prompt. Placeholder: GENDER_RULE.
        user_turn: Request for sentences. Placeholders: TILES, N.
        already_shown: Appended to the request in "different" mode. Placeholder: SHOWN.
    """

    system: str
    user_turn: str
    already_shown: str

    @classmethod
    def load(cls, directory: Path) -> "PromptTemplates":
        """
        Read system.md, user_turn.md and already_shown.md from a folder.

        Raises:
            ValueError: If a file has missing or unknown placeholders.
        """
        texts = {}
        for field, (filename, required) in _TEMPLATE_FILES.items():
            text = (directory / filename).read_text(encoding="utf-8").strip()
            found = set(_PLACEHOLDER.findall(text))
            if found != required:
                raise ValueError(
                    f"{filename}: expected placeholders {sorted(required)}, found {sorted(found)}"
                )
            texts[field] = text
        return cls(**texts)


def candidates_schema(n: int) -> dict[str, Any]:
    """
    JSON schema for the model response.

    Args:
        n: Maximum number of candidates.
    """
    return {
        "type": "object",
        "properties": {
            "candidates": {
                "type": "array",
                "minItems": 1,
                "maxItems": n,
                "items": {
                    "type": "object",
                    "properties": {
                        "urdu": {"type": "string"},
                        "english": {"type": "string"},
                        "style": {"type": "string", "enum": ["urdu", "code_mixed"]},
                    },
                    "required": ["urdu", "english", "style"],
                },
            }
        },
        "required": ["candidates"],
    }


def render_tiles(tiles: list[Tile]) -> str:
    """
    Render selected tiles as a numbered list for the prompt.
    """
    return "\n".join(
        f"{i}. {t.english} ({t.urdu}), {t.category}" for i, t in enumerate(tiles, start=1)
    )


def select_examples(examples: list[Example], selected: set[str], k: int) -> list[Example]:
    """
    Pick the k curated examples whose tile sets overlap the selection most.

    Ties keep the order of the example bank.

    Args:
        examples: The curated example bank.
        selected: Tile IDs of the current selection.
        k: Number of examples to return.
    """

    def score(example: Example) -> float:
        tile_set = set(example.tiles)
        return len(selected & tile_set) / len(selected | tile_set)

    ranked = sorted(enumerate(examples), key=lambda p: (-score(p[1]), p[0]))
    return [example for _, example in ranked[:k]]


def _user_turn(
    templates: PromptTemplates, tiles: list[Tile], n: int, exclude: list[str] | None = None
) -> str:
    turn = render(templates.user_turn, TILES=render_tiles(tiles), N=str(n))
    if exclude:
        shown = "\n".join(f"- {s}" for s in exclude)
        turn += "\n\n" + render(templates.already_shown, SHOWN=shown)
    return turn


def build_messages(
    templates: PromptTemplates,
    tiles: list[Tile],
    *,
    n: int,
    gender: Gender | None,
    exclude: list[str],
    shots: list[tuple[list[Tile], Example]],
) -> list[dict[str, str]]:
    """
    Build the chat messages for one suggestion request.

    The curated examples are given as earlier turns of the conversation, so the model sees the
    expected input and output format before the real request.

    Args:
        templates: The prompt texts.
        tiles: Selected tiles in selection order.
        n: Maximum number of sentences wanted.
        gender: Speaker gender, or None when unknown.
        exclude: Sentences already shown, which the model should not repeat.
        shots: Few-shot examples, each as (resolved tiles, example).
    """
    system = render(templates.system, GENDER_RULE=_GENDER_RULES[gender])
    messages = [{"role": "system", "content": system}]
    for shot_tiles, example in shots:
        messages.append({"role": "user", "content": _user_turn(templates, shot_tiles, n)})
        answer = {"candidates": [c.model_dump() for c in example.candidates]}
        messages.append({"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)})
    messages.append({"role": "user", "content": _user_turn(templates, tiles, n, exclude)})
    return messages
