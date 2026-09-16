from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Candidate:
    id: str
    title: str
    author: str | None
    text: str
    source_url: str | None = None
    source_name: str | None = None
    language: str = "zh-CN"
    category: str | None = None
    published_year: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def work_id(self) -> str:
        return str(self.metadata.get("work_id") or self.id)


@dataclass(slots=True)
class EvaluatedCandidate:
    candidate: Candidate
    literary_quality: int
    depth: int
    language_quality: int
    read_aloud_quality: int
    emotional_value: int
    excerpt_quality: int
    timelessness: int
    final_score: float
    reason: str = ""
    diversity_bonus: float = 0.0
    repetition_penalty: float = 0.0


@dataclass(slots=True)
class HistoryEntry:
    id: str
    datetime: str
    title: str
    author: str | None
    category: str | None
    work_id: str
    text_hash: str
    score: float

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "HistoryEntry":
        return cls(
            id=str(raw.get("id", "")),
            datetime=str(raw.get("datetime", "")),
            title=str(raw.get("title", "")),
            author=raw.get("author"),
            category=raw.get("category"),
            work_id=str(raw.get("work_id", "")),
            text_hash=str(raw.get("text_hash", "")),
            score=float(raw.get("score", 0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Article:
    id: str
    datetime: str
    title: str
    author: str | None
    work: str
    category: str | None
    recommendation: str
    introduction: str
    excerpt: str
    afterword: str
    source_name: str | None
    source_url: str | None
    audio: str | None
    reading_time: int
    tags: list[str]
    score: dict[str, float]
    original_text_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def article_to_history(article: Article) -> HistoryEntry:
    return HistoryEntry(
        id=article.id,
        datetime=article.datetime,
        title=article.title,
        author=article.author,
        category=article.category,
        work_id=article.work,
        text_hash=article.original_text_hash,
        score=float(article.score.get("overall", 0)),
    )
