from publish import markdown_to_html, publish_article


class FakePublisher:
    def create_post(self, *, title, content, slug, metadata=None):
        return {"status": "DRAFT", "post_id": 123, "slug": slug, "link": "https://example.com/test"}


def test_markdown_to_html_converts_basic_content():
    result = markdown_to_html("## Why it matters\n\nThis is **useful**.")
    assert "<h2>Why it matters</h2>" in result
    assert "<strong>useful</strong>" in result


def test_publish_article_uses_publisher_and_returns_result():
    article = {
        "title": "Test Buying Guide",
        "slug": "test-buying-guide",
        "body_markdown": "A short article.",
    }
    result = publish_article(article, publisher=FakePublisher())
    assert result["status"] == "DRAFT"
    assert result["post_id"] == 123
    assert result["slug"] == "test-buying-guide"


def test_publish_article_requires_title():
    try:
        publish_article({"body_markdown": "content"}, publisher=FakePublisher())
    except ValueError as exc:
        assert "title" in str(exc)
    else:
        raise AssertionError("Expected missing title to fail")
