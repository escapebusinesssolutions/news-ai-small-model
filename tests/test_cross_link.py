from cross_link import add_internal_links, cross_link, select_related


def test_select_related_prefers_same_category_and_overlap():
    article = {"title": "Best wireless keyboards", "slug": "best-wireless-keyboards", "category": "keyboards"}
    existing = [
        {"title": "Wireless keyboards for work", "slug": "wireless-work", "category": "keyboards", "url": "https://example.com/wireless-work"},
        {"title": "Best monitors", "slug": "best-monitors", "category": "monitors", "url": "https://example.com/monitors"},
    ]
    assert select_related(article, existing)[0]["slug"] == "wireless-work"


def test_cross_link_skips_self_and_limits_links():
    article = {"title": "Best wireless keyboards", "slug": "best-wireless-keyboards", "body_markdown": "Intro", "category": "keyboards"}
    existing = [
        {"title": "Wireless keyboards for work", "slug": "wireless-work", "category": "keyboards", "url": "https://example.com/wireless-work"},
        {"title": "Mechanical keyboards", "slug": "mechanical", "category": "keyboards", "url": "https://example.com/mechanical"},
        {"title": "Best keyboards", "slug": "keyboards", "category": "keyboards", "url": "https://example.com/keyboards"},
        {"title": "Another keyboard guide", "slug": "another", "category": "keyboards", "url": "https://example.com/another"},
    ]
    result = cross_link(article, existing)
    assert "best-wireless-keyboards" not in str(result["related_articles"])
    assert result["body_markdown"].count("https://example.com/") == 3


def test_add_internal_links_leaves_article_unchanged_without_matches():
    body = "Intro"
    assert add_internal_links(body, []) == body
