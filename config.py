"""Small Model runtime configuration.

Secrets belong in environment variables / GitHub Actions secrets, never in source control.
"""

import os

WORDPRESS_SITE_ID = os.getenv("WORDPRESS_SITE_ID", "")
WORDPRESS_ACCESS_TOKEN = os.getenv("WORDPRESS_ACCESS_TOKEN", "")
WORDPRESS_PUBLISH_ENABLED = os.getenv("WORDPRESS_PUBLISH_ENABLED", "false").lower() == "true"
WORDPRESS_DEFAULT_STATUS = os.getenv("WORDPRESS_DEFAULT_STATUS", "draft")
WORDPRESS_TIMEOUT_SECONDS = os.getenv("WORDPRESS_TIMEOUT_SECONDS", "30")

AI_PROVIDER = os.getenv("AI_PROVIDER", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")

