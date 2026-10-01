import json
from typing import Any


def extract_json_object(text: str) -> dict[str, Any]:
    """
    Parse the first JSON object found in model output.

    Some models ignore the requested JSON schema and wrap the object in a Markdown code fence
    or surround it with prose. This returns the first complete object either way.

    Args:
        text: Raw model output.

    Returns:
        The parsed JSON object.

    Raises:
        ValueError: If the text contains no JSON object.
    """
    decoder = json.JSONDecoder()
    start = text.find("{")
    while start != -1:
        try:
            obj, _ = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            start = text.find("{", start + 1)
            continue
        if isinstance(obj, dict):
            return obj
        start = text.find("{", start + 1)
    raise ValueError("no JSON object in model output")
