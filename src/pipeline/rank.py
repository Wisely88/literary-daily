from __future__ import annotations

import re
from collections import Counter

from ..models import Candidate, EvaluatedCandidate, HistoryEntry


def score_candidate(candidate: Candidate, history: list[HistoryEntry], category_weights: dict[str, float]) -> EvaluatedCandidate:
    length = len(candidate.text)
    length_score = 100 if 800 <= length <= 3500 else max(40, 100 - abs(length - 2000) / 30)
    paragraph_score = min(100, 50 + len(re.findall(r"[。！？]", candidate.text)) * 2)
    diversity = _diversity_bonus(candidate, history)
    category_bonus = min(5, category_weights.get(candidate.category or "", 0) / 5)
    repetition_penalty = 0 if diversity else 8
    parts = {
        "literary_quality": round((length_score * 0.55) + (paragraph_score * 0.45)),
        "depth": round(min(100, 55 + len(candidate.text) / 80)),
        "language_quality": round(paragraph_score),
        "read_aloud_quality": round(min(100, 55 + len(re.findall(r"[，。！？；：]", candidate.text)) * 1.5)),
        "emotional_value": round(min(100, 55 + len(re.findall(r"我|心|夜|梦|孤独|生命|山|月", candidate.text)) * 2)),
        "excerpt_quality": round(length_score),
        "timelessness": round(60 + category_bonus * 5),
    }
    overall = sum(parts.values()) / len(parts) + diversity + category_bonus - repetition_penalty
    return EvaluatedCandidate(candidate=candidate, final_score=round(overall, 2), reason="规则评分：篇幅、句读、朗读节奏与近期内容多样性均衡。", diversity_bonus=diversity, repetition_penalty=repetition_penalty, **parts)


def _diversity_bonus(candidate: Candidate, history: list[HistoryEntry]) -> float:
    recent = history[-10:]
    categories = Counter(entry.category for entry in recent)
    return 4.0 if candidate.category and categories[candidate.category] == 0 else 0.0
