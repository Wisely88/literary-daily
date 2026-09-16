from __future__ import annotations

from datetime import datetime

from ..models import Article, Candidate, EvaluatedCandidate, HistoryEntry
from ..pipeline.extract import extract_excerpt
from ..pipeline.rank import score_candidate
from ..utils.dates import run_id
from ..utils.hashing import text_hash


class HeuristicEvaluator:
    def __init__(self, category_weights: dict[str, float]) -> None:
        self.category_weights = category_weights

    def evaluate(self, candidate: Candidate, history: list[HistoryEntry]) -> EvaluatedCandidate:
        return score_candidate(candidate, history, self.category_weights)


class HeuristicEditor:
    def edit(self, selected: EvaluatedCandidate, moment: datetime, excerpt_min: int, excerpt_max: int) -> Article:
        candidate = selected.candidate
        excerpt = extract_excerpt(candidate.text, excerpt_min, excerpt_max)
        assert excerpt in candidate.text
        article_id = run_id(moment, candidate.title)
        recommendation = f"今晚想推荐这篇文字，是因为它在{len(excerpt)}字里保留了清晰的情绪与余韵，适合慢慢读完。"
        introduction = f"{candidate.author or '这位作者'}的《{candidate.title}》来自{candidate.source_name or '候选文学内容'}，保留原文片段，适合在一段安静时间里阅读。"
        afterword = "先不急着寻找结论。留意文字如何在具体的景物、动作和停顿之间，让情绪慢慢显影。"
        tts_text = f"《{candidate.title}》。作者：{candidate.author or '佚名'}。{recommendation}\n{excerpt}"
        return Article(
            id=article_id,
            datetime=moment.isoformat(),
            title=candidate.title,
            author=candidate.author,
            work=candidate.metadata.get("work_id", candidate.id),
            category=candidate.category,
            recommendation=recommendation,
            introduction=introduction,
            excerpt=excerpt,
            afterword=afterword,
            source_name=candidate.source_name,
            source_url=candidate.source_url,
            audio=None,
            reading_time=max(1, round(len(excerpt) / 350)),
            tags=[candidate.category] if candidate.category else [],
            score={"overall": selected.final_score, "literary": selected.literary_quality, "depth": selected.depth, "language": selected.language_quality},
            original_text_hash=text_hash(candidate.text),
        )
