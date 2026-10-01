import unicodedata

URDU_FULL_STOP = "۔"
URDU_QUESTION_MARK = "؟"
URDU_COMMA = "،"

# The zero-width non-joiner is part of Urdu orthography, so it is the one format character allowed.
ZWNJ = "‌"

_ARABIC_BLOCKS = ((0x0600, 0x06FF), (0x0750, 0x077F))


def reject_hidden_characters(text: str) -> str:
    """
    Reject control and invisible formatting characters.

    Control characters (newlines, tabs) and format characters (direction overrides, zero-width
    spaces) can change how text displays or is spoken. The zero-width non-joiner is allowed.

    Args:
        text: The text to check.

    Returns:
        The text unchanged.

    Raises:
        ValueError: If the text contains a disallowed character.
    """
    for ch in text:
        if ch != ZWNJ and unicodedata.category(ch) in ("Cc", "Cf"):
            raise ValueError(f"disallowed character U+{ord(ch):04X}")
    return text


def count_letters(text: str) -> tuple[int, int]:
    """
    Count Urdu-script letters and Latin letters.

    Args:
        text: The text to inspect.

    Returns:
        A pair (arabic_script_letters, latin_letters). Punctuation, digits and spaces are not
        counted.
    """
    arabic = latin = 0
    for ch in text:
        if not unicodedata.category(ch).startswith("L"):
            continue
        if any(lo <= ord(ch) <= hi for lo, hi in _ARABIC_BLOCKS):
            arabic += 1
        elif ch.isascii():
            latin += 1
    return arabic, latin


def comparison_key(text: str) -> str:
    """
    Reduce text to a key for comparing sentences.

    The key ignores case, spacing and punctuation, so two renderings of the same sentence
    that differ only in those compare equal.

    Args:
        text: The sentence.

    Returns:
        The normalized key.
    """
    text = unicodedata.normalize("NFC", text).casefold()
    return "".join(ch for ch in text if unicodedata.category(ch)[0] in ("L", "N", "M"))
