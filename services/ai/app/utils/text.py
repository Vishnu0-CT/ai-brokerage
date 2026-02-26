from __future__ import annotations


def strip_fences(text: str) -> str:
    """Remove markdown code fences from around text."""
    text = text.strip()
    if text.startswith("```"):
        text = text[text.index("\n") + 1:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()
