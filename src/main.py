from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .ai.fallback import HeuristicEditor, HeuristicEvaluator
from .ai.gemini import GeminiProvider, GeminiProviderError
from .audio.tts import GeminiTTSProvider, generate_audio
from .collectors.local_library import LocalLibraryCollector
from .collectors.rss import RSSCollector
from .collectors.webpage import WebpageCollector
from .config import Settings
from .models import Article, EvaluatedCandidate, HistoryEntry, article_to_history
from .pipeline.deduplicate import deduplicate
from .pipeline.normalize import normalize_candidates, rule_filter
from .site.generator import build_site
from .utils.dates import now_iso, run_id
from .utils.hashing import text_hash
from .utils.logging import configure_logging, stage


def main() -> None:
    args = parse_args()
    root = Path(__file__).parents[1]
    settings = Settings.load(root, Path(args.config).resolve() if args.config else None)
    configure_logging(args.debug)
    run(settings, category=args.category or None, force=args.force, dry_run=args.dry_run, skip_tts=args.skip_tts)


def run(settings: Settings, *, category: str | None = None, force: bool = False, dry_run: bool = False, skip_tts: bool = False) -> Article:
    data_dir = settings.root / "data"
    history = _load_history(data_dir / "history.json")
    moment = now_iso(settings.timezone)
    candidates = _collect(settings)
    stage("COLLECT", f"{len(candidates)} candidates")
    candidates = normalize_candidates(candidates)
    candidates = rule_filter(candidates, settings.min_chars, settings.max_chars)
    stage("FILTER", f"{len(candidates)} remaining")
    if category:
        candidates = [candidate for candidate in candidates if candidate.category == category or candidate.metadata.get("category_key") == category]
    if not force:
        candidates = deduplicate(candidates, history, moment, settings.history_dedupe_days, settings.same_author_cooldown_days, settings.same_work_cooldown_days)
    stage("DEDUP", f"{len(candidates)} remaining")
    if not candidates:
        raise RuntimeError("No eligible literary candidates remain")

    gemini = GeminiProvider(settings.ai_model, settings.ai_temperature, prompts=settings.prompts)
    heuristic = HeuristicEvaluator(settings.category_weights)
    evaluated: list[EvaluatedCandidate] = []
    for candidate in candidates[: settings.ai_max_candidates]:
        try:
            evaluated.append(gemini.evaluate(candidate, history))
        except GeminiProviderError as exc:
            logging.warning("[RANK] Gemini unavailable; using deterministic fallback (%s)", str(exc))
            evaluated.append(heuristic.evaluate(candidate, history))
    evaluated.sort(key=lambda item: item.final_score, reverse=True)
    stage("RANK", f"evaluated {len(evaluated)}")
    selected = evaluated[0]
    stage("SELECT", f"{selected.candidate.title} / score={selected.final_score}")

    article = _edit_article(gemini, selected, moment, settings)
    if not dry_run and not skip_tts and settings.tts_enabled:
        audio_relative = Path("audio") / moment.strftime("%Y") / moment.strftime("%m") / f"{article.id}.{settings.tts_format}"
        audio_path = settings.root / audio_relative
        if generate_audio(GeminiTTSProvider(settings.tts_model, settings.tts_voice), _tts_text(article), audio_path):
            article.audio = audio_relative.as_posix()
    stage("TTS", "generated" if article.audio else "skipped or unavailable")
    if dry_run:
        print(json.dumps(article.to_dict(), ensure_ascii=False, indent=2))
        return article

    articles = [article.to_dict()] + _load_articles(data_dir / "articles.json")
    _write_json(data_dir / "articles.json", articles[: settings.archive_size])
    _write_json(data_dir / "history.json", [entry.to_dict() for entry in history + [article_to_history(article)]])
    _write_json(data_dir / "state.json", {"last_run": article.datetime, "last_success": article.datetime, "total_articles": len(articles), "recent_categories": [item.get("category") for item in articles[:10]], "recent_authors": [item.get("author") for item in articles[:10]], "recent_works": [item.get("work") for item in articles[:10]]})
    build_site(articles, settings.root, settings.archive_size)
    stage("SITE", "OK")
    return article


def _collect(settings: Settings):
    sources = settings.sources
    results = []
    local = sources.get("local_library", {})
    if local.get("enabled", True):
        content_dir = (settings.root / str(local.get("path", "library"))).resolve()
        authors_dir = (settings.root / str(local.get("authors_path", "library/authors"))).resolve()
        results.extend(LocalLibraryCollector(content_dir, authors_dir).collect(settings.candidate_target))
    rss = sources.get("rss", {})
    if rss.get("enabled"):
        results.extend(RSSCollector(list(rss.get("urls", []))).collect(settings.candidate_target))
    webpages = sources.get("webpages", {})
    if webpages.get("enabled"):
        results.extend(WebpageCollector(list(webpages.get("urls", []))).collect(settings.candidate_target))
    return results[: settings.candidate_target]


def _edit_article(gemini: GeminiProvider, selected: EvaluatedCandidate, moment, settings: Settings) -> Article:
    try:
        raw = gemini.edit(selected, moment.isoformat())
        candidate = selected.candidate
        excerpt = str(raw["excerpt"])
        if excerpt not in candidate.text:
            raise GeminiProviderError("excerpt integrity check failed")
        return Article(id=run_id(moment, candidate.title), datetime=moment.isoformat(), title=candidate.title, author=candidate.author, work=candidate.work_id, category=candidate.category, recommendation=str(raw["recommendation"]), introduction=str(raw["introduction"]), excerpt=excerpt, afterword=str(raw["afterword"]), source_name=candidate.source_name, source_url=candidate.source_url, audio=None, reading_time=max(1, round(len(excerpt) / 350)), tags=[str(tag) for tag in raw.get("tags", [])], score={"overall": selected.final_score, "literary": selected.literary_quality, "depth": selected.depth, "language": selected.language_quality}, original_text_hash=text_hash(candidate.text))
    except GeminiProviderError as exc:
        logging.warning("[EDIT] Gemini unavailable; using deterministic editor (%s)", str(exc))
        return HeuristicEditor().edit(selected, moment, settings.excerpt_min, settings.excerpt_max)


def _tts_text(article: Article) -> str:
    return f"《{article.title}》。作者：{article.author or '佚名'}。{article.recommendation}\n{article.excerpt}"


def _load_history(path: Path) -> list[HistoryEntry]:
    if not path.exists():
        return []
    return [HistoryEntry.from_dict(item) for item in json.loads(path.read_text(encoding="utf-8"))]


def _load_articles(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="每日文学批量精选与静态发布")
    parser.add_argument("--config")
    parser.add_argument("--category")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-tts", action="store_true")
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    main()
