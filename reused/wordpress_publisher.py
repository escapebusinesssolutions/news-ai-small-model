from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class WordPressConfig:
    site_url: str
    username: str
    application_password: str
    publish_enabled: bool = False
    post_status: str = "draft"
    timeout_seconds: int = 30

    @classmethod
    def from_env(cls) -> "WordPressConfig":
        return cls(
            site_url=os.getenv("WORDPRESS_SITE_URL", "https://techsignal.wasmer.app").rstrip("/"),
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
        if self.publish_enabled and not self.username or self.publish_enabled and not self.application_password:
            raise RuntimeError("WordPress publishing needs WORDPRESS_USERNAME and WORDPRESS_APP_PASSWORD")


class WordPressPublisher:
    def __init__(self, config: WordPressConfig | None = None) -> None:
        self.config = config or WordPressConfig.from_env()
        self.config.validate()

    @property
    def _api_base(self) -> str:
        return f"{self.config.site_url}/wp-json/wp/v2"

    def _auth(self) -> tuple[str, str] | None:
        if not self.config.username or not self.config.application_password:
            return None
        return self.config.username, self.config.application_password

    def healthcheck(self) -> dict[str, Any]:
        response = requests.get(
            f"{self.config.site_url}/wp-json/",
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "ok": True,
            "name": data.get("name"),
            "url": data.get("url"),
            "api_url": f"{self.config.site_url}/wp-json/",
        }

    def authorization_check(self) -> dict[str, Any]:
        auth = self._auth()
        if not auth:
            return {"ok": False, "authorized": False, "reason": "WordPress Application Password missing"}
        response = requests.get(
            f"{self._api_base}/users/me",
            auth=auth,
            timeout=self.config.timeout_seconds,
        )
        if response.status_code in {401, 403}:
            return {"ok": False, "authorized": False, "reason": f"WordPress authentication rejected ({response.status_code})"}
        response.raise_for_status()
        user = response.json()
        return {
            "ok": True,
            "authorized": True,
            "user_id": user.get("id"),
            "username": user.get("slug") or user.get("name"),
            "roles": user.get("roles", []),
        }

    def create_post(self, *, title: str, content: str, slug: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        status = self.config.post_status if self.config.publish_enabled else "draft"
        payload: dict[str, Any] = {"title": title, "content": content, "status": status, "slug": slug}
        if not self.config.publish_enabled:
            return {
                "status": "DRY_RUN",
                "publish_enabled": False,
                "payload": payload,
                "endpoint": f"{self._api_base}/posts",
            }
        auth = self._auth()
        if not auth:
            raise RuntimeError("WordPress publishing needs WORDPRESS_USERNAME and WORDPRESS_APP_PASSWORD")
        response = requests.post(
            f"{self._api_base}/posts",
            auth=auth,
            json=payload,
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "status": "PUBLISHED" if status == "publish" else status.upper(),
            "post_id": data.get("id"),
            "link": data.get("link"),
            "slug": data.get("slug"),
            "status_value": data.get("status"),
        }


def stable_slug(title: str, event_id: str) -> str:
    base = "-".join(title.lower().split())[:75]
    suffix = hashlib.sha256(event_id.encode("utf-8")).hexdigest()[:8]
    return f"{base}-{suffix}".strip("-")
