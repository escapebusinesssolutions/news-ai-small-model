"""Small Model configuration.

Secrets belong in environment variables / GitHub Actions secrets, never in source control.
"""

import os

WORDPRESS_URL = os.getenv("WORDPRESS_URL", "")
WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME", "")
WORDPRESS_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD", "")

AI_PROVIDER = os.getenv("AI_PROVIDER", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")
