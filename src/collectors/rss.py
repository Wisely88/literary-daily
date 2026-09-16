from __future__ import annotations

import html
import logging
import re
import urllib.request
import xml.etree.ElementTree as ET

from .local_library import candidate_from_feed
from ..models import Candidate


def _plain(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


class RSSCollector:
    name = "rss"

    def __init__(self, urls: list[str], timeout: float = 10) -> None:
        self.urls = urls
        self.timeout = timeout

    def collect(self, limit: int) -> list[Candidate]:
        results: list[Candidate] = []
        for url in self.urls:
            try:
                with urllib.request.urlopen(url, timeout=self.timeout) as response:
                    root = ET.fromstring(response.read())
                for item in root.findall(".//item"):
                    title = _plain(item.findtext("title", ""))
                    link = _plain(item.findtext("link", ""))
                    text = _plain(item.findtext("description", "") or item.findtext("summary", ""))
                    if title and text:
                        results.append(candidate_from_feed(title, text, link or url, url))
                        if len(results) >= limit:
                            return results
            except (OSError, ET.ParseError) as exc:
                logging.warning("[COLLECT] RSS failed for %s: %s", url, type(exc).__name__)
        return results
