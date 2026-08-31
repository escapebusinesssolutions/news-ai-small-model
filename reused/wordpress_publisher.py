from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any

import requests

WP_API = "https://public-api.wordpress.com"


@dataclass(frozen=True)
class WordPressConfig:
    site_id: str
    access_token: str
    username: str
    application_password: str
    client_id: str
    client_secret: str
    publish_enabled: bool = False
    post_status: str = "draft"
    timeout_seconds: int = 30

    @classmethod
    def from_env(cls) -> "WordPressConfig":
        return cls(
            site_id=os.getenv("WORDPRESS_SITE_ID", "257062637"),
            access_token=os.getenv("WORDPRESS_ACCESS_TOKEN", ""),
            username=os.getenv("WORDPRESS_USERNAME", ""),
            application_password=os.getenv("WORDPRESS_APP_PASSWORD", ""),
            client_id=os.getenv("WORDPRESS_CLIENT_ID", ""),
            client_secret=os.getenv("WORDPRESS_CLIENT_SECRET", ""),
            publish_enabled=os.getenv("WORDPRESS_PUBLISH_ENABLED", "false").lower() == "true",
            post_status=os.getenv("WORDPRESS_DEFAULT_STATUS", "draft"),
            timeout_seconds=int(os.getenv("WORDPRESS_TIMEOUT_SECONDS", "30")),
        )

    def validate(self) -> None:
        if not self.site_id:
            raise RuntimeError("WORDPRESS_SITE_ID is not configured")
        if self.post_status not in {"draft", "pending", "private", "publish"}:
            raise RuntimeError(f"Unsupported WordPress post status: {self.post_status}")
        if self.publish_enabled and not self.access_token and not all(
            [self.username, self.application_password, self.client_id, self.client_secret]
        ):
            raise RuntimeError(
                "WordPress publishing needs WORDPRESS_ACCESS_TOKEN or the four token-exchange credentials"
            )


class WordPressPublisher:
    def __init__(self, config: WordPressConfig | None = None) -> None:
        self.config = config or WordPressConfig.from_env()
        self.config.validate()
        self._token = self.config.access_token or self._exchange_application_password()

    def _exchange_application_password(self) -> str:
        if not all(
            [
                self.config.username,
                self.config.application_password,
                self.config.client_id,
                self.config.client_secret,
            ]
        ):
            return ""
        response = requests.post(
            f"{WP_API}/oauth2/token",
            data={
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "grant_type": "password",
                "username": self.config.username,
                "password": self.config.application_password,
            },
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        token = str(response.json().get("access_token", ""))
        if not token:
            raise RuntimeError("WordPress OAuth token response did not contain access_token")
        return token

    def _site_url(self) -> str:
        return f"{WP_API}/rest/v1.2/sites/{self.config.site_id}"

    def _posts_url(self) -> str:
        return f"{WP_API}/rest/v1.1/sites/{self.config.site_id}/posts/new"

    def _headers(self) -> dict[str, str]:
        if not self._token:
            return {"Content-Type": "application/json"}
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def healthcheck(self) -> dict[str, Any]:
        response = requests.get(self._site_url(), timeout=self.config.timeout_seconds)
        response.raise_for_status()
        data = response.json()
        return {
            "ok": True,
            "site_id": data.get("ID"),
            "name": data.get("name"),
            "url": data.get("URL"),
            "is_wpcom_atomic": data.get("is_wpcom_atomic"),
            "jetpack": data.get("jetpack"),
        }

    def authorization_check(self) -> dict[str, Any]:
        if not self._token:
            return {"ok": False, "authorized": False, "reason": "WordPress OAuth token missing"}
        response = requests.get(
            self._site_url(),
            headers=self._headers(),
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        site = response.json()
        if str(site.get("ID")) != str(self.config.site_id):
            return {
                "ok": False,
                "authorized": False,
                "reason": "Configured site identity mismatch",
                "site_id": self.config.site_id,
            }
        capabilities = site.get("capabilities", {})
        if isinstance(capabilities, list):
            capabilities = {name: True for name in capabilities}
        publish_posts = bool(capabilities.get("publish_posts"))
        edit_posts = bool(capabilities.get("edit_posts"))
        return {
            "ok": publish_posts,
            "authorized": True,
            "site_id": site.get("ID"),
            "url": site.get("URL"),
            "publish_posts": publish_posts,
            "edit_posts": edit_posts,
        }

    def create_post(self, *, title: str, content: str, slug: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        status = self.config.post_status if self.config.publish_enabled else "draft"
        payload: dict[str, Any] = {"title": title, "content": content, "status": status, "slug": slug}
        if not self.config.publish_enabled:
            return {
                "status": "DRY_RUN",
                "publish_enabled": False,
                "payload": payload,
                "endpoint": self._posts_url(),
            }
        response = requests.post(
            self._posts_url(),
            headers=self._headers(),
            json=payload,
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "status": "PUBLISHED" if status == "publish" else status.upper(),
            "post_id": data.get("id") or data.get("ID"),
            "link": data.get("link") or data.get("URL") or data.get("short_URL"),
            "slug": data.get("slug"),
            "status_value": data.get("status"),
        }


def stable_slug(title: str, event_id: str) -> str:
    base = "-".join(title.lower().split())[:75]
    suffix = hashlib.sha256(event_id.encode("utf-8")).hexdigest()[:8]
    return f"{base}-{suffix}".strip("-")
