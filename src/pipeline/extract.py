from __future__ import annotations


def extract_excerpt(text: str, minimum: int = 1000, maximum: int = 3000) -> str:
    """Select whole paragraphs and never synthesize or truncate source text."""
    paragraphs = [part.strip() for part in text.split("\n") if part.strip()]
    if not paragraphs:
        return text
    if len(text) <= maximum:
        return text
    best = paragraphs[0]
    best_distance = float("inf")
    for start in range(len(paragraphs)):
        current: list[str] = []
        length = 0
        for paragraph in paragraphs[start:]:
            projected = length + len(paragraph) + (1 if current else 0)
            if projected > maximum:
                break
            current.append(paragraph)
            length = projected
            if length >= minimum and abs(length - (minimum + maximum) / 2) < best_distance:
                best = "\n".join(current)
                best_distance = abs(length - (minimum + maximum) / 2)
    return best
