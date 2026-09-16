from __future__ import annotations

import json
import os
import urllib.request

from ..models import Article


class PushPlusNotifier:
    """Send a rendered article notification to a personal WeChat via PushPlus."""

    def __init__(
        self,
        token: str | None = None,
        endpoint: str = "https://www.pushplus.plus/send",
        template: str = "markdown",
    ) -> None:
        self.token = token or os.getenv("PUSHPLUS_TOKEN", "")
        self.endpoint = endpoint
        self.template = template

    def send(self, article: Article | dict, base_url: str) -> None:
        if not self.token:
            raise RuntimeError("PushPlus credentials are not configured")
        data = article.to_dict() if isinstance(article, Article) else article
        link = f"{base_url.rstrip('/')}/articles/{data['id']}.html"
        title = f"📖 文学精选｜《{data['title']}》"
        content = (
            "## 📖 文学精选\n"
            f"### 《{data['title']}》\n"
            f"作者：{data.get('author') or '佚名'}\n\n"
            f"> {data['recommendation']}\n\n"
            f"约 {data.get('reading_time', 1)} 分钟阅读\n\n"
            f"[阅读全文 / 收听]({link})"
        )
        payload = json.dumps(
            {"token": self.token, "title": title, "content": content, "template": self.template},
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
        if result.get("code") not in (0, 200, "0", "200"):
            raise RuntimeError("PushPlus rejected notification")
