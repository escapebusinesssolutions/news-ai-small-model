"""Lightweight internal cross-linking."""
import re

MAX_LINKS = 3


def _words(value):
    return {w for w in re.findall(r"[a-z0-9]+", value.lower()) if len(w) > 3}


def select_related(article, existing_articles, limit=MAX_LINKS):
    article_words = _words(str(article.get("title", "")) + " " + str(article.get("source_topic", "")))
    category = str(article.get("category", "")).strip().lower()
    product_names = [str(p.get("name", "")).strip().casefold() for p in article.get("products", []) if isinstance(p, dict)]
    candidates = []
    for item in existing_articles:
        if str(item.get("slug", "")).strip() == str(article.get("slug", "")).strip():
            continue
        title = str(item.get("title", "")).strip()
        url = str(item.get("url", "")).strip()
        if not title or not url:
            continue
        # Do not create a related-article link to an older duplicate of the same
        # primary product; it can create circular or stale recommendation paths.
        if any(name and name in title.casefold() for name in product_names):
            continue
        score = len(article_words & _words(title))
        if category and category == str(item.get("category", "")).strip().lower():
            score += 3
        if score > 0:
            candidates.append((score, item))
    candidates.sort(key=lambda pair: (-pair[0], str(pair[1].get("title", "")).lower()))
    return [item for _, item in candidates[:max(0, limit)]]


def add_internal_links(body_markdown, related, limit=MAX_LINKS):
    links = []
    seen = set()
    for item in related:
        title = str(item.get("title", "")).strip()
        url = str(item.get("url", "")).strip()
        if not title or not url or url in seen:
            continue
        seen.add(url)
        links.append(f"- [{title}]({url})")
        if len(links) >= limit:
            break
    if not links:
        return body_markdown
    return body_markdown.rstrip() + "\n\n## Related articles\n" + "\n".join(links) + "\n"


def cross_link(article, existing_articles, limit=MAX_LINKS):
    """Return a copy with up to three relevant internal links."""
    result = dict(article)
    related = select_related(article, existing_articles, limit)
    result["body_markdown"] = add_internal_links(str(article.get("body_markdown", "")), related, limit)
    result["related_articles"] = related
    return result
