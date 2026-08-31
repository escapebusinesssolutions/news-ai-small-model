from cross_link import cross_link
from pipeline import run_pipeline


def test_pipeline_order_with_stubs(monkeypatch):
    calls = []

    def fake_generate(topic):
        calls.append("generate")
        return {"title": "Keyboards", "slug": "keyboards", "body_markdown": "Body", "products": [], "category": "keyboards", "source_topic": topic["topic"]}

    def fake_affiliate(article):
        calls.append("affiliate")
        return article

    def fake_cross(article, existing):
        calls.append("cross_link")
        return article

    def fake_publish(article):
        calls.append("publish")
        return {"status": "DRY_RUN"}

    monkeypatch.setattr("pipeline.generate_article", fake_generate)
    monkeypatch.setattr("pipeline.insert_affiliate_links", fake_affiliate)
    monkeypatch.setattr("pipeline.cross_link", fake_cross)
    monkeypatch.setattr("pipeline.publish_article", fake_publish)

    result = run_pipeline({"topic": "test", "category": "keyboards"}, existing_articles=[], publish=False)
    assert result["publish_result"]["status"] == "DRY_RUN"
    assert calls == ["generate", "affiliate", "cross_link", "publish"]


def test_pipeline_can_use_existing_articles_without_network(monkeypatch):
    monkeypatch.setattr("pipeline.generate_article", lambda topic: {
        "title": "Wireless Keyboards",
        "slug": "wireless-keyboards",
        "body_markdown": "Body",
        "products": [],
        "category": "keyboards",
        "source_topic": topic["topic"],
    })
    monkeypatch.setattr("pipeline.insert_affiliate_links", lambda article: article)
    monkeypatch.setattr("pipeline.publish_article", lambda article: {"status": "DRY_RUN"})

    result = run_pipeline(
        {"topic": "wireless keyboards", "category": "keyboards"},
        existing_articles=[{"title": "Best Mechanical Keyboards", "url": "https://example.com/mechanical", "slug": "mechanical"}],
        publish=False,
    )
    assert result["related_articles"]
