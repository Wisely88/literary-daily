from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

from ..models import Article


class TelegramNotifier:
    def __init__(self, token: str | None = None, chat_id: str | None = None) -> None:
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")

    def send(self, article: Article | dict, base_url: str) -> None:
        if not self.token or not self.chat_id:
            raise RuntimeError("Telegram credentials are not configured")
        data = article.to_dict() if isinstance(article, Article) else article
        link = f"{base_url.rstrip('/')}/articles/{urllib.parse.quote(str(data['id']))}.html"
        text = f"📖 今日的文学精选\n《{data['title']}》\n作者：{data.get('author') or '佚名'}\n\n{data['recommendation']}\n约 {data.get('reading_time', 1)} 分钟阅读\n🔗 {link}"
        payload = urllib.parse.urlencode({"chat_id": self.chat_id, "text": text}).encode()
        request = urllib.request.Request(f"https://api.telegram.org/bot{self.token}/sendMessage", data=payload, method="POST")
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not result.get("ok"):
            raise RuntimeError("Telegram rejected notification")
