from typing import Any

from app.schemas import Candidate
from app.textutil import (
    URDU_COMMA,
    URDU_FULL_STOP,
    URDU_QUESTION_MARK,
    comparison_key,
    count_letters,
    reject_hidden_characters,
)

MAX_URDU_CHARS = 120
MAX_ENGLISH_CHARS = 160

# Characters that signal leaked notes, markup or formatting rather than a sentence.
_LEAK_CHARS = set("()[]{}<>:*#`_|\\")
_SENTENCE_END = ".!?" + URDU_FULL_STOP + URDU_QUESTION_MARK


def _clean_urdu(text: str) -> str | None:
    """
    Normalize the Urdu text of one candidate, or return None if it is not a clean sentence.
    """
    text = text.strip()
    if not text or len(text) > MAX_URDU_CHARS or any(c in _LEAK_CHARS for c in text):
        return None
    arabic, latin = count_letters(text)
    if arabic == 0 or latin > arabic:
        return None
    is_question = text.rstrip().endswith(("?", URDU_QUESTION_MARK))
    body = text.rstrip(_SENTENCE_END + " ")
    body = body.replace(",", URDU_COMMA).replace("?", URDU_QUESTION_MARK)
    if not body:
        return None
    return body + (URDU_QUESTION_MARK if is_question else URDU_FULL_STOP)


def _clean_english(text: str) -> str | None:
    """
    Normalize the English text of one candidate, or return None if it is not a clean sentence.
    """
    text = text.strip()
    if not text or len(text) > MAX_ENGLISH_CHARS or any(c in _LEAK_CHARS for c in text):
        return None
    arabic, latin = count_letters(text)
    if latin == 0 or arabic > 0:
        return None
    return text if text[-1] in ".!?" else text + "."


def clean_candidates(raw: dict[str, Any], n: int, exclude: list[str]) -> list[Candidate]:
    """
    Validate and normalize the candidates in a model response.

    Candidates are dropped when they are malformed, contain hidden or markup characters, are too
    long, are not mostly Urdu script, have non-English translations, repeat an earlier candidate,
    or match a sentence in the exclude list. A candidate containing Latin letters is marked
    code_mixed. Order is preserved, so the model's ranking is kept.

    Args:
        raw: The parsed JSON object returned by the model.
        n: Maximum number of candidates to return.
        exclude: Urdu sentences that should not be returned.

    Returns:
        At most n clean candidates, possibly none.
    """
    items = raw.get("candidates")
    if not isinstance(items, list):
        return []

    seen_urdu = {comparison_key(s) for s in exclude}
    seen_english: set[tuple[str, str]] = set()
    out: list[Candidate] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        urdu, english = item.get("urdu"), item.get("english")
        if not isinstance(urdu, str) or not isinstance(english, str):
            continue
        try:
            reject_hidden_characters(urdu)
            reject_hidden_characters(english)
        except ValueError:
            continue
        urdu, english = _clean_urdu(urdu), _clean_english(english)
        if urdu is None or english is None:
            continue

        _, latin = count_letters(urdu)
        style = "code_mixed" if latin > 0 or item.get("style") == "code_mixed" else "urdu"

        urdu_key = comparison_key(urdu)
        english_key = (comparison_key(english), style)
        if urdu_key in seen_urdu or english_key in seen_english:
            continue
        seen_urdu.add(urdu_key)
        seen_english.add(english_key)
        out.append(Candidate(urdu=urdu, english=english, style=style))
        if len(out) == n:
            break
    return out
