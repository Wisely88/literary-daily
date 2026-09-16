from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from src.config import Settings
from src.notification import PushPlusNotifier, TelegramNotifier


def main() -> None:
    root = Path(__file__).parents[1]
    settings = Settings.load(root)
    articles = json.loads((root / "data" / "articles.json").read_text(encoding="utf-8"))
    if not articles or not settings.notification_enabled:
        return
    base_url = os.getenv("PAGES_BASE_URL") or settings.base_url
    providers = []
    if "telegram" in settings.notification_providers and os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
        providers.append(("Telegram", lambda: TelegramNotifier().send(articles[0], base_url)))
    if "pushplus" in settings.notification_providers and os.getenv("PUSHPLUS_TOKEN"):
        providers.append(("PushPlus", lambda: PushPlusNotifier(endpoint=settings.pushplus_endpoint, template=settings.pushplus_template).send(articles[0], base_url)))
    if not providers:
        raise RuntimeError("No notification provider credentials are configured")
    failures = []
    for name, send in providers:
        try:
            send()
            logging.info("[NOTIFY] %s sent", name)
        except Exception as exc:  # noqa: BLE001 - one provider must not hide another
            logging.error("[NOTIFY] %s failed: %s", name, exc)
            failures.append(name)
    if failures:
        raise RuntimeError(f"Notification failed for: {', '.join(failures)}")


if __name__ == "__main__":
    main()
