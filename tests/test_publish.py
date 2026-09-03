import publish
from publish import markdown_to_html, publish_article


class FakePublisher:
    def create_post(self, *, title, content, slug, metadata=None):
        return {"status": "DRAFT", "post_id": 123, "slug": slug, "link": "https://example.com/test"}


def test_markdown_to_html_converts_basic_content():
    result = markdown_to_html("## Why it matters\n\nThis is **useful**.")
    assert "<h2>Why it matters</h2>" in result
    assert "<strong>useful</strong>" in result


def test_publish_article_uses_verified_external_images(monkeypatch):
    monkeypatch.setattr(publish, "build_article_images", lambda plan: [
        {"role": "hero", "url": "https://commons.wikimedia.org/example-hero.jpg", "alt_text": "Desk microphone", "caption": "A desk microphone.", "source_page": "https://commons.wikimedia.org/wiki/File:Example.jpg", "source": "Wikimedia Commons", "license": "CC BY", "license_url": "https://creativecommons.org/licenses/by/4.0/", "artist": ""},
        {"role": "context", "url": "https://commons.wikimedia.org/example-context.jpg", "alt_text": "Person speaking into a microphone", "caption": "A voice recording setup.", "source_page": "https://commons.wikimedia.org/wiki/File:Example2.jpg", "source": "Wikimedia Commons", "license": "CC BY", "license_url": "https://creativecommons.org/licenses/by/4.0/", "artist": ""},
    ])
    article = {
        "title": "Test Buying Guide",
        "slug": "test-buying-guide",
        "body_markdown": "## Why it matters\n\nA useful article.",
        "image_plan": [{"role": "hero", "search_query": "microphone desk"}, {"role": "context", "search_query": "person microphone"}],
    }
    result = publish_article(article, publisher=FakePublisher())
    assert result["status"] == "DRAFT"
    assert result["post_id"] == 123
    assert result["slug"] == "test-buying-guide"
    assert result["stored_in_wordpress_media"] is False


def test_publish_article_requires_title():
    try:
        publish_article({"body_markdown": "content"}, publisher=FakePublisher())
    except ValueError as exc:
        assert "title" in str(exc)
    else:
        raise AssertionError("Expected missing title to fail")
