"""Publish generated Small Model articles through the WordPress publisher."""
from __future__ import annotations

import html
import re
from typing import Any

from reused.wordpress_publisher import WordPressPublisher


def _inline_markdown(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def markdown_to_html(markdown: str) -> str:
    """Convert predictable article Markdown into clean WordPress HTML."""
    lines = markdown.strip().splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    in_list = False
    in_table = False

    def flush() -> None:
        if paragraph:
            text = " ".join(part.strip() for part in paragraph)
            output.append(f"<p>{_inline_markdown(text)}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    def close_table() -> None:
        nonlocal in_table
        if in_table:
            output.append("</tbody></table>")
            in_table = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            flush(); close_list()
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                continue
            if not in_table:
                output.append("<table><thead><tr>" + "".join(f"<th>{_inline_markdown(c)}</th>" for c in cells) + "</tr></thead><tbody>")
                in_table = True
            else:
                output.append("<tr>" + "".join(f"<td>{_inline_markdown(c)}</td>" for c in cells) + "</tr>")
            continue
        if in_table:
            close_table()
        if stripped.startswith("### "):
            flush(); close_list(); output.append(f"<h3>{_inline_markdown(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            flush(); close_list(); output.append(f"<h2>{_inline_markdown(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            flush(); close_list(); output.append(f"<h2>{_inline_markdown(stripped[2:])}</h2>")
        elif re.match(r"^[-*+]\s+", stripped):
            flush()
            if not in_list:
                output.append("<ul>")
                in_list = True
            item = re.sub(r"^[-*+]\s+", "", stripped, count=1)
            output.append(f"<li>{_inline_markdown(item)}</li>")
        else:
            close_list()
            paragraph.append(stripped)

    flush(); close_list(); close_table()
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
    result = wp.create_post(title=title, content=html_body, slug=slug, metadata={"category": article.get("category", "")})
    return {**result, "title": title, "slug": slug}


if __name__ == "__main__":
    raise SystemExit("Use publish_article(article) from the pipeline; no article is published from an empty command-line invocation.")
