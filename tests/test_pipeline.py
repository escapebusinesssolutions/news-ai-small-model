from pipeline import build_validation_report, run_pipeline
from same_day_dedup import TopicFingerprint, select_non_duplicate_topic


def _article():
    return {
        "title": "Keyboards",
        "slug": "keyboards",
        "body_markdown": "Body",
        "products": [{
            "name": "Keyboard A",
            "asin_or_id": "A1",
            "affiliate_url": "https://www.amazon.co.uk/dp/A1?tag=echsignalnews-21",
            "affiliate_link_type": "catalogue",
        }],
        "affiliate_tracking_id": "echsignalnews-21",
        "affiliate_marketplace": "amazon.co.uk",
        "affiliate_exact_matches": 1,
        "affiliate_search_links": 0,
    }


def test_pipeline_order_with_stubs(monkeypatch):
    calls = []
    monkeypatch.setattr("pipeline.generate_article", lambda topic: calls.append("generate") or _article())
    monkeypatch.setattr("pipeline.insert_affiliate_links", lambda article: calls.append("affiliate") or article)
    monkeypatch.setattr("pipeline.cross_link", lambda article, existing: calls.append("cross_link") or article)

    result = run_pipeline({"topic": "test", "category": "keyboards"}, existing_articles=[], publish=False)

    assert result["validation_report"]["validation"]["passed"] is True
    assert calls == ["generate", "affiliate", "cross_link"]


def test_pipeline_publishes_only_after_validation(monkeypatch):
    calls = []
    article = _article()
    monkeypatch.setattr("pipeline.generate_article", lambda topic: calls.append("generate") or article)
    monkeypatch.setattr("pipeline.insert_affiliate_links", lambda value: calls.append("affiliate") or value)
    monkeypatch.setattr("pipeline.cross_link", lambda value, existing: calls.append("cross_link") or value)
    monkeypatch.setattr("pipeline.publish_article", lambda value: calls.append("publish") or {"status": "DRAFT"})

    result = run_pipeline({"topic": "test", "category": "keyboards"}, existing_articles=[], publish=True)

    assert result["status"] == "DRAFT"
    assert calls == ["generate", "affiliate", "cross_link", "publish"]


def test_pipeline_blocks_publish_when_validation_fails(monkeypatch):
    article = _article()
    article["products"][0]["affiliate_url"] = "https://example.com/not-amazon"
    publish_called = []
    monkeypatch.setattr("pipeline.generate_article", lambda topic: article)
    monkeypatch.setattr("pipeline.insert_affiliate_links", lambda value: value)
    monkeypatch.setattr("pipeline.cross_link", lambda value, existing: value)
    monkeypatch.setattr("pipeline.publish_article", lambda value: publish_called.append(True))

    try:
        run_pipeline({"topic": "test", "category": "keyboards"}, existing_articles=[], publish=True)
    except ValueError as exc:
        assert "Pre-publish validation failed" in str(exc)
    else:
        raise AssertionError("Expected invalid affiliate URL to block publication")

    assert publish_called == []


def test_validation_report_records_exact_affiliate_links():
    report = build_validation_report(_article(), {"topic": "test", "category": "keyboards"})

    assert report["validation"]["passed"] is True
    assert report["affiliate"]["products_selected"] == 1
    assert report["affiliate"]["exact_catalogue_matches"] == 1
    assert report["affiliate"]["search_links"] == 0
    assert report["affiliate"]["links"][0]["affiliate_url"] == "https://www.amazon.co.uk/dp/A1?tag=echsignalnews-21"


def test_pipeline_can_use_existing_articles_without_network(monkeypatch):
    monkeypatch.setattr("pipeline.generate_article", lambda topic: _article())
    monkeypatch.setattr("pipeline.insert_affiliate_links", lambda article: article)
    monkeypatch.setattr("pipeline.cross_link", lambda article, existing: {**article, "cross_links": existing})

    result = run_pipeline(
        {"topic": "wireless keyboards", "category": "keyboards"},
        existing_articles=[{"title": "Best Mechanical Keyboards", "url": "https://example.com/mechanical", "slug": "mechanical"}],
        publish=False,
    )
    assert result["cross_links"]


def test_same_day_dedup_advances_to_next_topic(monkeypatch, tmp_path):
    import same_day_dedup as dedup
    dedup.DEDUP_LOG_PATH = tmp_path / "published_today.json"
    dedup.record_published_fingerprint(TopicFingerprint.from_story_record({"topic": "USB microphones", "category": "audio"}))
    topics = [
        {"topic": "USB microphones", "category": "audio"},
        {"topic": "portable SSD backups", "category": "storage"},
    ]
    selected, index = select_non_duplicate_topic(topics, 0, max_attempts=2)
    assert index == 1
    assert selected["topic"] == "portable SSD backups"
