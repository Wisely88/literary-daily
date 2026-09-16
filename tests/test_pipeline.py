from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from src.models import Candidate, HistoryEntry
from src.pipeline.deduplicate import deduplicate
from src.pipeline.extract import extract_excerpt
from src.pipeline.normalize import normalize_candidates, rule_filter
from src.notification.pushplus import PushPlusNotifier
from src.site.generator import build_site


class PipelineTests(unittest.TestCase):
    def test_normalize_and_filter_removes_navigation_and_short_text(self):
        candidates = [Candidate("a", "  A  ", "作者", "一段文字 " * 200), Candidate("b", "B", None, "短")]
        result = rule_filter(normalize_candidates(candidates), 300, 6000)
        self.assertEqual(["A"], [item.title for item in result])

    def test_deduplicate_blocks_same_text_and_recent_author(self):
        now = datetime.fromisoformat("2026-09-16T08:30:00+08:00")
        candidate = Candidate("a", "新标题", "同作者", "文学内容 " * 100, metadata={"work_id": "new"})
        history = [HistoryEntry("h", "2026-09-10T08:30:00+08:00", "旧标题", "同作者", "散文", "old", "different", 90)]
        self.assertEqual([], deduplicate([candidate], history, now))

    def test_excerpt_is_contiguous_and_never_exceeds_maximum(self):
        text = "\n".join("段落" + str(index) + "：" + "文字" * 100 for index in range(20))
        excerpt = extract_excerpt(text, 300, 600)
        self.assertIn(excerpt, text)
        self.assertLessEqual(len(excerpt), 600)

    def test_static_site_contains_escaped_article_and_audio(self):
        article = {"id": "20260916-0830-demo", "title": "<安全>", "author": "作者", "category": "散文", "recommendation": "推荐", "introduction": "背景", "excerpt": "正文\n第二段", "afterword": "小记", "source_name": "本地", "source_url": None, "audio": "audio/2026/09/demo.mp3", "reading_time": 3, "tags": [], "score": {"overall": 90}, "original_text_hash": "hash"}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "templates").mkdir()
            (root / "static/css").mkdir(parents=True)
            (root / "static/js").mkdir(parents=True)
            (root / "templates/index.html").write_text("$latest $archive", encoding="utf-8")
            (root / "templates/article.html").write_text("$title $excerpt $audio", encoding="utf-8")
            (root / "static/css/main.css").write_text("", encoding="utf-8")
            (root / "static/js/reader.js").write_text("", encoding="utf-8")
            (root / "audio/2026/09").mkdir(parents=True)
            (root / "audio/2026/09/demo.mp3").write_bytes(b"audio")
            site = build_site([article], root)
            self.assertIn("&lt;安全&gt;", (site / "articles/20260916-0830-demo.html").read_text(encoding="utf-8"))
            self.assertTrue((site / "audio/2026/09/demo.mp3").exists())

    def test_pushplus_sends_markdown_payload_without_network(self):
        article = {
            "id": "20260916-0830-demo",
            "title": "示例文章",
            "author": "作者",
            "recommendation": "适合安静读完的一段文字。",
            "reading_time": 4,
        }

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b'{"code": 200, "msg": "success"}'

        with patch("src.notification.pushplus.urllib.request.urlopen", return_value=FakeResponse()) as mocked:
            PushPlusNotifier(token="test-token").send(article, "https://example.github.io/literary-daily")
        request = mocked.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["token"], "test-token")
        self.assertEqual(payload["template"], "markdown")
        self.assertIn("/articles/20260916-0830-demo.html", payload["content"])


if __name__ == "__main__":
    unittest.main()
