from insert_links import build_affiliate_url, insert_affiliate_links


def test_build_amazon_uk_affiliate_url():
    source = "https://www.amazon.co.uk/dp/B000IB9QXI/ref=nosim"
    result = build_affiliate_url(source, "techsignal-20")
    assert result == "https://www.amazon.co.uk/dp/B000IB9QXI/ref=nosim?tag=techsignal-20"


def test_replaces_existing_tracking_tag():
    source = "https://www.amazon.co.uk/dp/B000IB9QXI?tag=old-tag&ref=abc"
    result = build_affiliate_url(source, "techsignal-20")
    assert "tag=techsignal-20" in result
    assert "old-tag" not in result


def test_rejects_non_uk_amazon_domain():
    try:
        build_affiliate_url("https://www.amazon.de/dp/B000IB9QXI", "techsignal-20")
    except ValueError:
        return
    raise AssertionError("Non-UK Amazon URL should be rejected")


def test_inserts_matching_catalogue_link(tmp_path, monkeypatch):
    catalogue = tmp_path / "products.json"
    catalogue.write_text(
        '{"marketplace":"amazon.co.uk","tracking_id":"techsignal-20",'
        '"products":[{"name":"Example Keyboard","url":"https://www.amazon.co.uk/dp/B000IB9QXI"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr("insert_links.PRODUCTS_FILE", catalogue)
    article = {
        "title": "Example",
        "body_markdown": "A short guide.",
        "products": [{"name": "Example Keyboard", "why_it_is_relevant": "Test", "buying_note": "Test"}],
    }
    result = insert_affiliate_links(article)
    assert "tag=techsignal-20" in result["products"][0]["affiliate_url"]
    assert "techsignal-20" in result["body_markdown"]
