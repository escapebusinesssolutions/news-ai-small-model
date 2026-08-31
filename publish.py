"""Publish a generated Small Model article through the proven WordPress publisher."""
from __future__ import annotations

import html
import re
from typing import Any

from reused.wordpress_publisher import WordPressPublisher


def markdown_to_html(markdown: str) -> str:
    """Convert the small, predictable Markdown produced by Generate into HTML."""
    lines = markdown.strip().splitlines()
    output: list[str] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            text = " ".join(part.strip() for part in paragraph)
            text = html.escape(text)
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
            text = re.sub(r"\[(.+?)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', text)
            output.append(f"<p>{text}</p>")
            paragraph.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith("### "):
            flush()
            output.append(f"<h3>{html.escape(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            flush()
            output.append(f"<h2>{html.escape(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            flush()
            output.append(f"<h2>{html.escape(stripped[2:])}</h2>")
        elif stripped.startswith("- "):
            flush()
            if not output or not output[-1].startswith("<ul>"):
                output.append("<ul>")
            item = html.escape(stripped[2:])
            item = re.sub(r"\[(.+?)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', item)
            output.append(f"<li>{item}</li>")
        else:
            if output and output[-1] == "</ul>":
                output.append(f"<p>{html.escape(stripped)}</p>")
            else:
                paragraph.append(stripped)

    flush()
    if output and output[-1].startswith("<li>"):
        output.append("</ul>")
    return "\n".join(output)


def publish_article(article: dict[str, Any], publisher: WordPressPublisher | None = None) -> dict[str, Any]:
    title = str(article.get("title", "")).strip()
    body = str(article.get("body_html") or article.get("body_markdown") or "").strip()
    slug = str(article.get("slug", "")).strip()
    if not title:
        raise ValueError("Article title is required")
    if not body:
        raise ValueError("Article body is required")
    if not slug:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

    html_body = body if "<p>" in body or "<h2>" in body else markdown_to_html(body)
    wp = publisher or WordPressPublisher()
    result = wp.create_post(title=title, content=html_body, slug=slug)
    return {**result, "title": title, "slug": slug}


if __name__ == "__main__":
    raise SystemExit("Use publish_article(article) from the pipeline; no article is published from an empty command-line invocation.")
