from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _load_mapping(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(raw)
    except ImportError:
        loaded = json.loads(raw)
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected mapping in {path}")
    return loaded


@dataclass(slots=True)
class Settings:
    root: Path
    project_name: str = "每日文学"
    language: str = "zh-CN"
    timezone: str = "Asia/Shanghai"
    slots: tuple[str, ...] = ("08:30", "12:30", "18:30", "22:30")
    candidate_target: int = 30
    candidate_minimum: int = 10
    min_chars: int = 300
    preferred_chars_min: int = 800
    preferred_chars_max: int = 3500
    max_chars: int = 6000
    history_dedupe_days: int = 365
    same_author_cooldown_days: int = 30
    same_work_cooldown_days: int = 365
    excerpt_min: int = 1000
    excerpt_max: int = 3000
    ai_model: str = "gemini-2.5-flash"
    ai_temperature: float = 0.3
    ai_max_candidates: int = 15
    tts_enabled: bool = True
    tts_model: str = "gemini-2.5-flash-preview-tts"
    tts_voice: str = "Sulafat"
    tts_format: str = "mp3"
    tts_retain_days: int = 60
    archive_size: int = 500
    base_url: str = "https://wisely88.github.io/literary-daily"
    notification_enabled: bool = True
    notification_providers: tuple[str, ...] = ("telegram", "pushplus")
    pushplus_endpoint: str = "https://www.pushplus.plus/send"
    pushplus_template: str = "markdown"
    category_weights: dict[str, float] = field(default_factory=dict)
    sources: dict[str, Any] = field(default_factory=dict)
    prompts: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, root: Path, config_path: Path | None = None) -> "Settings":
        config_path = config_path or root / "config" / "settings.yaml"
        raw = _load_mapping(config_path)
        selection = raw.get("selection", {})
        content = raw.get("content", {})
        excerpt = content.get("excerpt", {})
        ai = raw.get("ai", {})
        tts = raw.get("tts", {})
        site = raw.get("site", {})
        notification = raw.get("notification", {})
        pushplus = notification.get("pushplus", {})
        categories = _load_mapping(root / "config" / "categories.yaml")
        prompts_path = root / "config" / "prompts.yaml"
        prompts = _load_mapping(prompts_path) if prompts_path.exists() else {}
        sources_path = root / "config" / "sources.yaml"
        sources = _load_mapping(sources_path) if sources_path.exists() else raw.get("sources", {})
        return cls(
            root=root,
            project_name=raw.get("project", {}).get("name", "每日文学"),
            language=raw.get("project", {}).get("language", "zh-CN"),
            timezone=raw.get("project", {}).get("timezone", "Asia/Shanghai"),
            slots=tuple(raw.get("schedule", {}).get("slots", cls.slots)),
            candidate_target=int(selection.get("candidate_target", 30)),
            candidate_minimum=int(selection.get("candidate_minimum", 10)),
            min_chars=int(selection.get("min_chars", 300)),
            preferred_chars_min=int(selection.get("preferred_chars_min", 800)),
            preferred_chars_max=int(selection.get("preferred_chars_max", 3500)),
            max_chars=int(selection.get("max_chars", 6000)),
            history_dedupe_days=int(selection.get("history_dedupe_days", 365)),
            same_author_cooldown_days=int(selection.get("same_author_cooldown_days", 30)),
            same_work_cooldown_days=int(selection.get("same_work_cooldown_days", 365)),
            excerpt_min=int(excerpt.get("preferred_chars_min", 1000)),
            excerpt_max=int(excerpt.get("preferred_chars_max", 3000)),
            ai_model=os.getenv("GEMINI_MODEL", ai.get("model", "gemini-2.5-flash")),
            ai_temperature=float(ai.get("temperature", 0.3)),
            ai_max_candidates=int(ai.get("max_candidates", 15)),
            tts_enabled=bool(tts.get("enabled", True)),
            tts_model=os.getenv("GEMINI_TTS_MODEL", tts.get("model", "gemini-2.5-flash-preview-tts")),
            tts_voice=os.getenv("GEMINI_TTS_VOICE", tts.get("voice", "Sulafat")),
            tts_format=str(tts.get("format", "mp3")),
            tts_retain_days=int(tts.get("retain_days", 60)),
            archive_size=int(site.get("archive_size", 500)),
            base_url=str(site.get("base_url", "")),
            notification_enabled=bool(notification.get("enabled", True)),
            notification_providers=tuple(str(item) for item in notification.get("providers", ("telegram", "pushplus"))),
            pushplus_endpoint=str(pushplus.get("endpoint", "https://www.pushplus.plus/send")),
            pushplus_template=str(pushplus.get("template", "markdown")),
            category_weights={key: float(value.get("target_weight", 0)) for key, value in categories.items()},
            sources=sources,
            prompts={key: str(value) for key, value in prompts.items()},
        )
