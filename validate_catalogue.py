"""Validate Amazon UK catalogue destinations and generated affiliate URLs."""
from __future__ import annotations

import json
import sys
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests

TRACKING_ID = "techsignal-20"
TIMEOUT = 20


def affiliate_url(product: dict) -> str:
    parsed = urlparse(product["url"])
    query = parse_qs(parsed.query, keep_blank_values=True)
    query["tag"] = [TRACKING_ID]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def main() -> int:
    with open("products.json", encoding="utf-8") as fh:
        catalogue = json.load(fh)

    products = catalogue.get("products", [])
    failures = []
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 NewsAISmallModel catalogue validator"})

    for product in products:
        name = product["name"]
        asin = product["asin_or_id"]
        base = product["url"]
        tagged = affiliate_url(product)
        parsed = urlparse(tagged)

        structural_ok = (
            parsed.scheme == "https"
            and parsed.netloc.lower() == "www.amazon.co.uk"
            and f"/dp/{asin}" in parsed.path
            and parse_qs(parsed.query).get("tag") == [TRACKING_ID]
        )
        if not structural_ok:
            failures.append(f"{name}: invalid affiliate URL structure: {tagged}")
            continue

        try:
            response = session.get(tagged, timeout=TIMEOUT, allow_redirects=True, stream=True)
            final = response.url
            response.close()
            final_host = urlparse(final).netloc.lower()
            if response.status_code >= 400:
                failures.append(f"{name}: HTTP {response.status_code} for {tagged}")
            elif not final_host.endswith("amazon.co.uk") and "amazon." not in final_host:
                failures.append(f"{name}: unexpected redirect host {final_host}")
            else:
                print(f"PASS | {name} | {asin} | {tagged} | HTTP {response.status_code}")
        except requests.RequestException as exc:
            failures.append(f"{name}: request failed: {exc}")

    print(f"Checked {len(products)} products with tracking tag {TRACKING_ID}")
    if failures:
        print("FAILURES:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("ALL CATALOGUE AFFILIATE LINKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
