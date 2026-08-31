from insert_links import build_affiliate_url, insert_affiliate_links, load_catalogue

# Block 1: the catalogue is the only allowed commercial inventory.


def test_build_amazon_uk_affiliate_url():
    source = "https://www.amazon.co.uk/dp/B000IB9QXI/ref=nosim"
    result = build_affiliate_url(source, "echsignalnews-21")
    assert result == "https://www.amazon.co.uk/dp/B000IB9QXI/ref=nosim?tag=echsignalnews-21"


def test_replaces_existing_tracking_tag():
    source = "https://www.amazon.co.uk/dp/B000IB9QXI?tag=old-tag&ref=abc"
    result = build_affiliate_url(source, "echsignalnews-21")
    assert "tag=echsignalnews-21" in result
    assert "old-tag" not in result


def test_rejects_non_uk_amazon_domain():
    try:
        build_affiliate_url("https://www.amazon.de/dp/B000IB9QXI", "echsignalnews-21")
    except ValueError:
        return
    raise AssertionError("Non-UK Amazon URL should be rejected")


def test_catalogue_has_valid_product_urls():
    catalogue = load_catalogue()
    assert catalogue["products"]
    for product in catalogue["products"]:
        assert product["asin_or_id"]
        assert f"/dp/{product['asin_or_id']}" in product["url"]


def test_inserts_exact_catalogue_link_by_name(tmp_path, monkeypatch):
    catalogue = tmp_path / "products.json"
    catalogue.write_text(
        '{"marketplace":"amazon.co.uk","tracking_id":"echsignalnews-21",'
        '"products":[{"name":"Example Keyboard","asin_or_id":"B000IB9QXI","url":"https://www.amazon.co.uk/dp/B000IB9QXI"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr("insert_links.PRODUCTS_FILE", catalogue)
    article = {
        "title": "Example",
        "body_markdown": "The Example Keyboard is a useful choice.",
        "products": [{"name": "Example Keyboard", "why_it_is_relevant": "Test", "buying_note": "Test"}],
    }
    result = insert_affiliate_links(article)
    assert result["products"][0]["asin_or_id"] == "B000IB9QXI"
    assert result["products"][0]["affiliate_link_type"] == "product"
    assert result["products"][0]["affiliate_url"] == "https://www.amazon.co.uk/dp/B000IB9QXI?tag=echsignalnews-21"
    assert "[Example Keyboard](https://www.amazon.co.uk/dp/B000IB9QXI?tag=echsignalnews-21)" in result["body_markdown"]
    assert result["affiliate_search_links"] == 0


def test_repairs_existing_product_markdown_link(tmp_path, monkeypatch):
    catalogue = tmp_path / "products.json"
    catalogue.write_text(
        '{"marketplace":"amazon.co.uk","tracking_id":"echsignalnews-21",'
        '"products":[{"name":"Example Keyboard","asin_or_id":"B000IB9QXI","url":"https://www.amazon.co.uk/dp/B000IB9QXI"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr("insert_links.PRODUCTS_FILE", catalogue)
    article = {
        "title": "Example",
        "body_markdown": "Try [Example Keyboard](https://www.amazon.co.uk/dp/OLDPRODUCT).",
        "products": [{"name": "Example Keyboard"}],
    }
    result = insert_affiliate_links(article)
    assert result["body_markdown"] == "Try [Example Keyboard](https://www.amazon.co.uk/dp/B000IB9QXI?tag=echsignalnews-21)."
    assert result["body_markdown"].count("[Example Keyboard]") == 1


def test_repairs_nested_product_markdown_link(tmp_path, monkeypatch):
    catalogue = tmp_path / "products.json"
    catalogue.write_text(
        '{"marketplace":"amazon.co.uk","tracking_id":"echsignalnews-21",'
        '"products":[{"name":"Example Keyboard","asin_or_id":"B000IB9QXI","url":"https://www.amazon.co.uk/dp/B000IB9QXI"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr("insert_links.PRODUCTS_FILE", catalogue)
    article = {
        "title": "Example",
        "body_markdown": "Try [Example Keyboard]([https://www.amazon.co.uk/dp/OLDPRODUCT](https://www.amazon.co.uk/dp/OLDPRODUCT)).",
        "products": [{"name": "Example Keyboard"}],
    }
    result = insert_affiliate_links(article)
    assert result["body_markdown"] == "Try [Example Keyboard](https://www.amazon.co.uk/dp/B000IB9QXI?tag=echsignalnews-21)."
    assert "][" not in result["body_markdown"]


def test_resolves_by_exact_catalogue_id(tmp_path, monkeypatch):
    catalogue = tmp_path / "products.json"
    catalogue.write_text(
        '{"marketplace":"amazon.co.uk","tracking_id":"echsignalnews-21",'
        '"products":[{"name":"Example Keyboard","asin_or_id":"B000IB9QXI","url":"https://www.amazon.co.uk/dp/B000IB9QXI"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr("insert_links.PRODUCTS_FILE", catalogue)
    article = {
        "title": "Example",
        "body_markdown": "A short guide.",
        "products": [{"name": "A slightly different name", "asin_or_id": "B000IB9QXI"}],
    }
    result = insert_affiliate_links(article)
    assert result["products"][0]["name"] == "Example Keyboard"
    assert result["products"][0]["asin_or_id"] == "B000IB9QXI"


def test_rejects_product_outside_catalogue(tmp_path, monkeypatch):
    catalogue = tmp_path / "products.json"
    catalogue.write_text(
        '{"marketplace":"amazon.co.uk","tracking_id":"echsignalnews-21",'
        '"products":[{"name":"Example Keyboard","asin_or_id":"B000IB9QXI","url":"https://www.amazon.co.uk/dp/B000IB9QXI"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr("insert_links.PRODUCTS_FILE", catalogue)
    article = {
        "title": "Example",
        "body_markdown": "A short guide.",
        "products": [{"name": "Unapproved Product", "why_it_is_relevant": "Test", "buying_note": "Test"}],
    }
    try:
        insert_affiliate_links(article)
    except ValueError as exc:
        assert "outside the approved catalogue" in str(exc)
        return
    raise AssertionError("Uncatalogued product must be rejected")


def test_rejects_partial_name_match(tmp_path, monkeypatch):
    catalogue = tmp_path / "products.json"
    catalogue.write_text(
        '{"marketplace":"amazon.co.uk","tracking_id":"echsignalnews-21",'
        '"products":[{"name":"Example Keyboard Pro","asin_or_id":"B000IB9QXI","url":"https://www.amazon.co.uk/dp/B000IB9QXI"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr("insert_links.PRODUCTS_FILE", catalogue)
    article = {
        "title": "Example",
        "body_markdown": "A short guide.",
        "products": [{"name": "Example Keyboard"}],
    }
    try:
        insert_affiliate_links(article)
    except ValueError as exc:
        assert "outside the approved catalogue" in str(exc)
        return
    raise AssertionError("Partial product-name matches must not select a catalogue item")


def test_rejects_catalogue_url_with_wrong_product_id(tmp_path, monkeypatch):
    catalogue = tmp_path / "products.json"
    catalogue.write_text(
        '{"marketplace":"amazon.co.uk","tracking_id":"echsignalnews-21",'
        '"products":[{"name":"Example Keyboard","asin_or_id":"B000IB9QXI","url":"https://www.amazon.co.uk/dp/B000AAAAAA"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr("insert_links.PRODUCTS_FILE", catalogue)
    try:
        load_catalogue()
    except ValueError as exc:
        assert "does not match asin_or_id" in str(exc)
        return
    raise AssertionError("Catalogue URL/ID mismatch must be rejected")
