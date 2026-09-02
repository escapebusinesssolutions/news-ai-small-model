"""Publish generated Small Model articles through the WordPress publisher."""
from __future__ import annotations

import html
import re
from typing import Any

from reused.images import build_article_images, images_to_html
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


def _insert_external_images(body_html: str, images: list[dict[str, Any]]) -> str:
    """Place the hero near the opening and context images between article sections."""
    if not images:
        raise ValueError("No compliant external images were found; publication is blocked")
    hero = next((image for image in images if image.get("role") == "hero"), None)
    if hero is None:
        raise ValueError("No compliant hero image was found; publication is blocked")
    context = [image for image in images if image.get("role") != "hero"]
    hero_html = images_to_html([hero])
    context_html = [images_to_html([image]) for image in context]

    parts = re.split(r"(?=<(?:h2|h3)>)", body_html, flags=re.I)
    if len(parts) > 1:
        body_html = parts[0] + hero_html + "\n" + "\n".join(parts[1:])
    else:
        paragraphs = body_html.split("</p>", 1)
        body_html = (paragraphs[0] + "</p>" + hero_html + paragraphs[1]) if len(paragraphs) == 2 else hero_html + body_html

    if context_html:
        sections = re.split(r"(?=<(?:h2|h3)>)", body_html, flags=re.I)
        inserts = min(len(context_html), max(0, len(sections) - 1))
        for index in range(inserts):
            sections[index + 1] = sections[index + 1] + "\n" + context_html[index]
        body_html = "".join(sections)
    return body_html


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

    image_plan = article.get("image_plan", [])
    images = build_article_images(image_plan)
    hero_count = sum(1 for image in images if image.get("role") == "hero")
    if hero_count != 1 or len(images) < 2:
        raise ValueError(
            f"External image gate failed: required 1 compliant hero + at least 1 context image; found {hero_count} hero and {len(images)} total"
        )
    html_body = _insert_external_images(html_body, images)

    wp = publisher or WordPressPublisher()
    result = wp.create_post(
        title=title,
        content=html_body,
        slug=slug,
        metadata={"category": article.get("category", ""), "external_images": images},
    )
    return {**result, "title": title, "slug": slug, "external_images": images, "stored_in_wordpress_media": False}


if __name__ == "__main__":
    raise SystemExit("Use publish_article(article) from the pipeline; no article is published from an empty command-line invocation.")
