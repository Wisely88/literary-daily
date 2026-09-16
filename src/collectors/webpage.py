from __future__ import annotations

import html
import logging
import re
import urllib.request
from html.parser import HTMLParser

from .local_library import candidate_from_feed
from ..models import Candidate


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "nav", "footer", "header", "form"}:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "nav", "footer", "header", "form"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)


class WebpageCollector:
    name = "webpage"

    def __init__(self, urls: list[str], timeout: float = 10) -> None:
        self.urls = urls
        self.timeout = timeout

    def collect(self, limit: int) -> list[Candidate]:
        results: list[Candidate] = []
        for url in self.urls:
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "literary-daily/1.0"})
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    source = response.read().decode("utf-8", errors="replace")
                parser = _TextParser()
                parser.feed(source)
                text = re.sub(r"\s+", " ", html.unescape(" ".join(parser.parts))).strip()
                title_match = re.search(r"<title[^>]*>(.*?)</title>", source, flags=re.I | re.S)
                title = re.sub(r"\s+", " ", html.unescape(title_match.group(1))).strip() if title_match else ""
                if title and text:
                    results.append(candidate_from_feed(title, text, url, url))
                    if len(results) >= limit:
                        break
            except (OSError, UnicodeError) as exc:
                logging.warning("[COLLECT] webpage failed for %s: %s", url, type(exc).__name__)
        return results
