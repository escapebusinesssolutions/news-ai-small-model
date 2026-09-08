from performance_intelligence import classify_pages


def test_classify_pages_links_live_wordpress_posts():
    performance = {
        "pages": [
            {"page": "https://techsignal.wasmer.app/a/", "clicks": 8, "impressions": 100, "ctr": 0.08, "position": 4},
            {"page": "https://techsignal.wasmer.app/b/", "clicks": 0, "impressions": 100, "ctr": 0.0, "position": 18},
        ]
    }
    posts = [{"id": 12, "link": "https://techsignal.wasmer.app/a/", "title": "Winner"}]
    result = classify_pages(performance, posts)
    assert result["pages"][0]["post_id"] == 12
    assert result["pages"][0]["title"] == "Winner"
    assert result["pages"][1]["classification"] == "underperformer"
    assert sum(result["counts"].values()) == 2
