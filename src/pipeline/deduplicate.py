from __future__ import annotations

from datetime import datetime, timedelta

from ..models import Candidate, HistoryEntry
from ..utils.hashing import normalize_title, text_hash


def deduplicate(
    candidates: list[Candidate],
    history: list[HistoryEntry],
    now: datetime,
    history_days: int = 365,
    author_days: int = 30,
    work_days: int = 365,
) -> list[Candidate]:
    cutoff = now - timedelta(days=history_days)
    recent = [entry for entry in history if _parse_date(entry.datetime) >= cutoff]
    seen_hashes: set[str] = set()
    results: list[Candidate] = []
    for candidate in candidates:
        digest = text_hash(candidate.text)
        title = normalize_title(candidate.title)
        if digest in seen_hashes or any(entry.text_hash == digest for entry in history):
            continue
        if any(entry.work_id == candidate.work_id and _parse_date(entry.datetime) >= now - timedelta(days=work_days) for entry in recent):
            continue
        if candidate.author and any(normalize_title(entry.author) == normalize_title(candidate.author) and _parse_date(entry.datetime) >= now - timedelta(days=author_days) for entry in recent):
            continue
        if any(normalize_title(entry.title) == title and _parse_date(entry.datetime) >= cutoff for entry in recent):
            continue
        seen_hashes.add(digest)
        results.append(candidate)
    return results


def _parse_date(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min
