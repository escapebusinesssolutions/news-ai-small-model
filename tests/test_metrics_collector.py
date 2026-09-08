import metrics_collector


def test_collect_search_performance_aggregates_and_ranks_pages(monkeypatch):
    monkeypatch.setattr(metrics_collector, "gsc_query", lambda *args, **kwargs: [
        {"keys": ["https://techsignal.example/a"], "clicks": 3, "impressions": 100, "ctr": 0.03, "position": 8.0},
        {"keys": ["https://techsignal.example/b"], "clicks": 7, "impressions": 50, "ctr": 0.14, "position": 4.0},
    ])

    result = metrics_collector.collect_search_performance("token", "2026-09-01", "2026-09-07")

    assert result["schema_version"] == "1.1"
    assert result["totals"] == {"clicks": 10.0, "impressions": 150.0, "ctr": 10 / 150}
    assert result["pages"][0]["page"].endswith("/b")
    assert result["pages"][0]["clicks"] == 7.0


def test_collect_search_performance_handles_empty_result(monkeypatch):
    monkeypatch.setattr(metrics_collector, "gsc_query", lambda *args, **kwargs: [])

    result = metrics_collector.collect_search_performance("token", "2026-09-01", "2026-09-07")

    assert result["totals"] == {"clicks": 0, "impressions": 0, "ctr": 0.0}
    assert result["pages"] == []
