import os
import sys
import requests

SITE = os.environ["WORDPRESS_SITE_URL"].rstrip("/")
USER = os.environ["WORDPRESS_USERNAME"]
PASSWORD = os.environ["WORDPRESS_APP_PASSWORD"]
AUTH = (USER, PASSWORD)
BASE = f"{SITE}/wp-json"

TITLE = "TechSignal — Tech Buying Guides, Reviews & Comparisons"
DESCRIPTION = "Independent tech buying guides, product reviews and comparisons to help you choose the right headphones, microphones, webcams, storage and more."
SNIPPET_NAME = "TechSignal SEO Foundation"

SNIPPET_CODE = r'''add_filter('pre_get_document_title', function ($title) {
    if (is_home() || is_front_page()) {
        return 'TechSignal — Tech Buying Guides, Reviews & Comparisons';
    }
    return $title;
}, 20);

add_action('wp_head', function () {
    if (is_home() || is_front_page()) {
        echo '<meta name="description" content="Independent tech buying guides, product reviews and comparisons to help you choose the right headphones, microphones, webcams, storage and more.">' . "\n";
        echo '<link rel="canonical" href="https://techsignal.wasmer.app/">' . "\n";
        echo '<style>.techsignal-home-h1{font-size:clamp(2rem,4vw,3.25rem);line-height:1.1;margin:0 0 1.5rem;font-weight:700}</style>' . "\n";
    }
}, 5);

add_action('blocksy:content:before', function () {
    if (is_home() || is_front_page()) {
        echo '<h1 class="techsignal-home-h1">Tech Buying Guides, Reviews &amp; Comparisons</h1>';
    }
}, 5);

add_action('template_redirect', function () {
    if (!empty($_SERVER['HTTP_HOST']) && str_starts_with(strtolower($_SERVER['HTTP_HOST']), 'www.')) {
        $target = 'https://techsignal.wasmer.app' . (isset($_SERVER['REQUEST_URI']) ? $_SERVER['REQUEST_URI'] : '/');
        wp_safe_redirect($target, 301);
        exit;
    }
});
'''


def request(method, url, **kwargs):
    r = requests.request(method, url, auth=AUTH, timeout=30, **kwargs)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {url} -> {r.status_code}: {r.text[:500]}")
    return r


def main():
    # Update core site identity. WordPress exposes these through /wp/v2/settings.
    request("POST", f"{BASE}/wp/v2/settings", json={"title": "TechSignal", "description": "Tech buying guides, reviews and comparisons."})

    # Install/activate the free Code Snippets plugin so the SEO fix survives theme updates.
    plugins = request("GET", f"{BASE}/wp/v2/plugins", params={"search": "code-snippets", "context": "view"}).json()
    active = any(p.get("plugin", "").startswith("code-snippets/") and p.get("status") == "active" for p in plugins)
    if not active:
        request("POST", f"{BASE}/wp/v2/plugins", json={"slug": "code-snippets", "status": "active"})

    # Create or update the idempotent SEO snippet.
    snippets_url = f"{BASE}/code-snippets/v1/snippets"
    existing = request("GET", snippets_url, params={"search": SNIPPET_NAME, "per_page": 100}).json()
    payload = {"name": SNIPPET_NAME, "desc": "Homepage title, meta description, H1 and canonical hostname redirect for TechSignal.", "code": SNIPPET_CODE, "scope": "global", "active": True, "priority": 5}
    match = next((x for x in existing if x.get("name") == SNIPPET_NAME), None)
    if match:
        request("POST", f"{snippets_url}/{match['id']}", json=payload)
        action = f"updated snippet {match['id']}"
    else:
        created = request("POST", snippets_url, json=payload).json()
        action = f"created snippet {created.get('id', '?')}"

    # Read back public HTML to prove the changes are actually live.
    html = requests.get(SITE + "/", timeout=30).text
    checks = {
        "title": "TechSignal — Tech Buying Guides, Reviews & Comparisons" in html,
        "meta_description": 'name="description"' in html and "Independent tech buying guides" in html,
        "h1": "<h1 class=\"techsignal-home-h1\">" in html,
        "canonical": 'rel="canonical"' in html and "https://techsignal.wasmer.app/" in html,
    }
    print({"site": SITE, "settings": "updated", "snippet": action, "checks": checks})
    if not all(checks.values()):
        print(html[:5000])
        sys.exit(2)


if __name__ == "__main__":
    main()
