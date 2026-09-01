from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class WordPressConfig:
    site_url: str
    site_id: str
    access_token: str
    username: str
    application_password: str
    publish_enabled: bool = False
    post_status: str = "draft"
    timeout_seconds: int = 30

    @classmethod
    def from_env(cls) -> "WordPressConfig":
        return cls(
            site_url=os.getenv("WORDPRESS_SITE_URL", "https://techsignal.wasmer.app").rstrip("/"),
            site_id=os.getenv("WORDPRESS_SITE_ID", "257062637"),
            access_token=os.getenv("WORDPRESS_ACCESS_TOKEN", ""),
            username=os.getenv("WORDPRESS_USERNAME", ""),
            application_password=os.getenv("WORDPRESS_APP_PASSWORD", ""),
            publish_enabled=os.getenv("WORDPRESS_PUBLISH_ENABLED", "false").lower() == "true",
            post_status=os.getenv("WORDPRESS_DEFAULT_STATUS", "draft"),
            timeout_seconds=int(os.getenv("WORDPRESS_TIMEOUT_SECONDS", "30")),
        )

    def validate(self) -> None:
        if not self.site_url.startswith(("https://", "http://")):
            raise RuntimeError("WORDPRESS_SITE_URL must be an HTTP(S) URL")
        if self.post_status not in {"draft", "pending", "private", "publish"}:
            raise RuntimeError(f"Unsupported WordPress post status: {self.post_status}")
        if self.publish_enabled and not self.access_token and not (self.username and self.application_password):
            raise RuntimeError("WordPress publishing needs WORDPRESS_ACCESS_TOKEN or username/application password")


class WordPressPublisher:
    def __init__(self, config: WordPressConfig | None = None) -> None:
        self.config = config or WordPressConfig.from_env()
        self.config.validate()

    @property
    def _api_base(self) -> str:
        return f"{self.config.site_url}/wp-json/wp/v2"

    @property
    def _wpcom_base(self) -> str:
        return f"https://public-api.wordpress.com/rest/v1.1/sites/{self.config.site_id}"

    def healthcheck(self) -> dict[str, Any]:
        response = requests.get(f"{self.config.site_url}/wp-json/", timeout=self.config.timeout_seconds)
        response.raise_for_status()
        data = response.json()
        return {"ok": True, "name": data.get("name"), "url": data.get("url"), "api_url": f"{self.config.site_url}/wp-json/"}

    def authorization_check(self) -> dict[str, Any]:
        if self.config.access_token:
            response = requests.get(f"{self._wpcom_base}/me", headers={"Authorization": f"Bearer {self.config.access_token}"}, timeout=self.config.timeout_seconds)
            if response.status_code in {401, 403}:
                return {"ok": False, "authorized": False, "reason": f"WordPress.com access token rejected ({response.status_code})"}
            response.raise_for_status()
            user = response.json()
            return {"ok": True, "authorized": True, "username": user.get("username") or user.get("display_name")}
        if not (self.config.username and self.config.application_password):
            return {"ok": False, "authorized": False, "reason": "WordPress credentials missing"}
        response = requests.get(f"{self._api_base}/users/me", auth=(self.config.username, self.config.application_password), timeout=self.config.timeout_seconds)
        if response.status_code in {401, 403}:
            return {"ok": False, "authorized": False, "reason": f"WordPress authentication rejected ({response.status_code})"}
        response.raise_for_status()
        user = response.json()
        return {"ok": True, "authorized": True, "user_id": user.get("id"), "username": user.get("slug") or user.get("name"), "roles": user.get("roles", [])}

    def _request(self, method: str, url: str, payload: dict[str, Any]) -> requests.Response:
        if self.config.access_token:
            return requests.request(method, url, headers={"Authorization": f"Bearer {self.config.access_token}"}, data=payload, timeout=self.config.timeout_seconds)
        return requests.request(method, url, auth=(self.config.username, self.config.application_password), json=payload, timeout=self.config.timeout_seconds)

    def _category_id(self, category: str) -> int | None:
        slug = str(category).strip().lower()
        if not slug:
            return None
        response = requests.get(f"{self._api_base}/categories", params={"slug": slug, "per_page": 1}, auth=(self.config.username, self.config.application_password), timeout=self.config.timeout_seconds)
        response.raise_for_status()
        existing = response.json()
        if existing:
            return int(existing[0]["id"])
        response = requests.post(f"{self._api_base}/categories", auth=(self.config.username, self.config.application_password), json={"name": slug.title(), "slug": slug}, timeout=self.config.timeout_seconds)
        response.raise_for_status()
        return int(response.json()["id"])

    def create_post(self, *, title: str, content: str, slug: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        status = self.config.post_status if self.config.publish_enabled else "draft"
        payload: dict[str, Any] = {"title": title, "content": content, "status": status, "slug": slug}
        category = (metadata or {}).get("category")
        if category and self.config.publish_enabled:
            category_id = self._category_id(str(category))
            if category_id is not None:
                payload["categories"] = [category_id]
        if not self.config.publish_enabled:
            return {"status": "DRY_RUN", "publish_enabled": False, "payload": payload, "endpoint": f"{self._api_base}/posts"}

        lookup = requests.get(f"{self._api_base}/posts", params={"slug": slug, "context": "edit"}, auth=(self.config.username, self.config.application_password), timeout=self.config.timeout_seconds)
        lookup.raise_for_status()
        existing = lookup.json()
        if existing:
            post_id = existing[0].get("id")
            response = self._request("PUT", f"{self._api_base}/posts/{post_id}", payload)
            response.raise_for_status()
            data = response.json()
            return {"status": "UPDATED", "post_id": data.get("id"), "link": data.get("link"), "slug": data.get("slug"), "status_value": data.get("status")}

        if self.config.access_token:
            response = requests.post(f"{self._wpcom_base}/posts/new", headers={"Authorization": f"Bearer {self.config.access_token}"}, data=payload, timeout=self.config.timeout_seconds)
        else:
            response = requests.post(f"{self._api_base}/posts", auth=(self.config.username, self.config.application_password), json=payload, timeout=self.config.timeout_seconds)
        response.raise_for_status()
        data = response.json()
        return {"status": "PUBLISHED" if status == "publish" else status.upper(), "post_id": data.get("ID") or data.get("id"), "link": data.get("URL") or data.get("link"), "slug": data.get("slug"), "status_value": data.get("status")}


def stable_slug(title: str, event_id: str) -> str:
    base = "-".join(title.lower().split())[:75]
    suffix = hashlib.sha256(event_id.encode("utf-8")).hexdigest()[:8]
    return f"{base}-{suffix}".strip("-")
