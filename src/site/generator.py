from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from string import Template

from ..models import Article


def build_site(articles: list[Article | dict], root: Path, archive_size: int = 500) -> Path:
    site_dir = root / "site"
    site_dir.mkdir(parents=True, exist_ok=True)
    static_source = root / "static"
    static_target = site_dir / "static"
    if static_source.exists():
        shutil.copytree(static_source, static_target, dirs_exist_ok=True)
    normalized = [article.to_dict() if isinstance(article, Article) else article for article in articles]
    normalized = normalized[:archive_size]
    (site_dir / "articles.json").write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    latest = normalized[:4]
    latest_html = "\n".join(_article_card(article) for article in latest) or '<p class="empty">还没有精选内容。</p>'
    archive_html = "\n".join(_archive_row(article) for article in normalized) or '<p class="empty">第一篇精选即将抵达。</p>'
    _write_template(root / "templates" / "index.html", site_dir / "index.html", {"title": "每日文学", "latest": latest_html, "archive": archive_html})
    for article in normalized:
        article_dir = site_dir / "articles"
        article_dir.mkdir(parents=True, exist_ok=True)
        article_html = _render_article(article, root)
        (article_dir / f"{article['id']}.html").write_text(article_html, encoding="utf-8")
        if article.get("audio"):
            audio_source = root / str(article["audio"])
            audio_target = site_dir / str(article["audio"])
            if audio_source.exists():
                audio_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(audio_source, audio_target)
    sitemap = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>", '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap.append("<url><loc>./</loc></url>")
    sitemap.extend(f"<url><loc>./articles/{html.escape(article['id'])}.html</loc></url>" for article in normalized)
    sitemap.append("</urlset>")
    (site_dir / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")
    validate_site(site_dir)
    return site_dir


def _write_template(template_path: Path, target: Path, values: dict[str, str]) -> None:
    template = Template(template_path.read_text(encoding="utf-8"))
    target.write_text(template.safe_substitute(values), encoding="utf-8")


def _article_card(article: dict) -> str:
    return f'''<article class="feature-card"><p class="kicker">{_e(article.get("category"))}</p><h2><a href="articles/{_e(article["id"])}.html">{_e(article["title"])}</a></h2><p class="byline">{_e(article.get("author") or "佚名")} · 约 {int(article.get("reading_time", 1))} 分钟</p><p>{_e(article.get("recommendation"))}</p><a class="text-link" href="articles/{_e(article["id"])}.html">阅读全文 →</a></article>'''


def _archive_row(article: dict) -> str:
    return f'''<li><a href="articles/{_e(article["id"])}.html"><span>{_e(article["title"])}</span><small>{_e(article.get("author") or "佚名")} · {_e(article.get("category"))}</small></a></li>'''


def _render_article(article: dict, root: Path) -> str:
    excerpt = "\n".join(f"<p>{_e(paragraph)}</p>" for paragraph in str(article.get("excerpt", "")).splitlines() if paragraph.strip())
    audio = f'<audio controls preload="metadata" src="../{_e(article["audio"])}"></audio>' if article.get("audio") else '<p class="muted">本篇暂未生成朗读音频。</p>'
    source = f'<a href="{_e(article["source_url"])}" rel="noreferrer">{_e(article.get("source_name") or "原始出处")}</a>' if article.get("source_url") else _e(article.get("source_name") or "本地 curated library")
    template_path = root / "templates" / "article.html"
    values = {
        "title": _e(article.get("title")), "author": _e(article.get("author") or "佚名"), "category": _e(article.get("category")),
        "recommendation": _e(article.get("recommendation")), "introduction": _e(article.get("introduction")), "excerpt": excerpt,
        "afterword": _e(article.get("afterword")), "audio": audio, "source": source, "article_id": _e(article.get("id")),
    }
    return Template(template_path.read_text(encoding="utf-8")).safe_substitute(values)


def _e(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def validate_site(site_dir: Path) -> None:
    index = site_dir / "index.html"
    articles_path = site_dir / "articles.json"
    if not index.exists() or not articles_path.exists():
        raise RuntimeError("Static site is missing index.html or articles.json")
    articles = json.loads(articles_path.read_text(encoding="utf-8"))
    for article in articles:
        page = site_dir / "articles" / f"{article['id']}.html"
        if not page.exists() or not article.get("excerpt"):
            raise RuntimeError(f"Static site validation failed for {article.get('id', 'unknown')}")
        audio = article.get("audio")
        if audio and not (site_dir / audio).exists():
            raise RuntimeError(f"Missing audio asset: {audio}")
