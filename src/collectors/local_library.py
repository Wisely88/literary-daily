from __future__ import annotations

import json
import re
from pathlib import Path

from ..models import Candidate
from ..utils.hashing import stable_id


def _frontmatter(source: str) -> dict[str, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", source, flags=re.S)
    if not match:
        return {}
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _section(source: str, heading: str) -> str:
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)", source, flags=re.M)
    return match.group(1).strip() if match else ""


class LocalLibraryCollector:
    name = "local_library"

    def __init__(self, content_dir: Path, authors_dir: Path | None = None) -> None:
        self.content_dir = content_dir
        self.authors_dir = authors_dir
        self._authors: dict[str, str] = {}
        if authors_dir and authors_dir.exists():
            for path in authors_dir.glob("*.json"):
                try:
                    raw = json.loads(path.read_text(encoding="utf-8"))
                    if raw.get("id") and raw.get("name"):
                        self._authors[str(raw["id"])] = str(raw["name"])
                except (OSError, ValueError):
                    continue

    def collect(self, limit: int) -> list[Candidate]:
        candidates: list[Candidate] = []
        for path in sorted(self.content_dir.glob("*.md")):
            raw = path.read_text(encoding="utf-8")
            meta = _frontmatter(raw)
            text = _section(raw, "原文") or _section(raw, "正文")
            if not meta.get("title") or not text:
                continue
            author_id = meta.get("authorId", "")
            candidates.append(
                Candidate(
                    id=meta.get("id", path.stem),
                    title=meta["title"],
                    author=self._authors.get(author_id) or author_id or None,
                    text=text,
                    source_name="本地 curated library",
                    language=meta.get("language", "zh-CN"),
                    category=meta.get("category"),
                    metadata={"work_id": meta.get("id", path.stem), "path": str(path), "rights_status": meta.get("rightsStatus")},
                )
            )
            if len(candidates) >= limit:
                break
        return candidates


def candidate_from_feed(title: str, text: str, url: str, source_name: str) -> Candidate:
    return Candidate(
        id=stable_id(title, url),
        title=title,
        author=None,
        text=text,
        source_url=url,
        source_name=source_name,
        metadata={"work_id": stable_id(title, url)},
    )
