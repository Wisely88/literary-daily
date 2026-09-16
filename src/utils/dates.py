from __future__ import annotations

from datetime import datetime
import hashlib
import re
from zoneinfo import ZoneInfo


def now_iso(timezone: str = "Asia/Shanghai") -> datetime:
    return datetime.now(ZoneInfo(timezone))


def run_id(moment: datetime, title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40]
    if not slug:
        slug = hashlib.sha256(title.encode("utf-8")).hexdigest()[:8]
    return f"{moment:%Y%m%d-%H%M}-{slug}"
