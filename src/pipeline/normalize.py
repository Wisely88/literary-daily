from __future__ import annotations

import re

from ..models import Candidate
from ..utils.hashing import normalize_text


def normalize_candidates(candidates: list[Candidate]) -> list[Candidate]:
    normalized: list[Candidate] = []
    for candidate in candidates:
        title = normalize_text(candidate.title)
        text = normalize_text(candidate.text)
        text = re.sub(r"(?:登录|注册|广告|上一篇|下一篇)\s*", " ", text)
        if title and text:
            candidate.title, candidate.text = title, text
            normalized.append(candidate)
    return normalized


def rule_filter(candidates: list[Candidate], min_chars: int, max_chars: int) -> list[Candidate]:
    return [
        candidate
        for candidate in candidates
        if (min_chars <= len(candidate.text) or _is_short_poetry(candidate))
        and len(candidate.text) <= max_chars
        and candidate.title
        and not _looks_like_navigation(candidate.text)
    ]


def _is_short_poetry(candidate: Candidate) -> bool:
    return "诗" in (candidate.category or "") or "词" in (candidate.category or "")


def _looks_like_navigation(text: str) -> bool:
    if len(text) < 500:
        return False
    navigation_words = len(re.findall(r"首页|目录|登录|注册|版权|免责声明", text))
    return navigation_words >= 5 and navigation_words / max(len(text), 1) > 0.01
