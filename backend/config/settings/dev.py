"""Development settings (local machine, GitHub Codespaces, Claude Code cloud sessions)."""

import os

from config.env import env_bool, env_list, env_str

from .base import *  # noqa: F403
from .base import FRONTEND_URL, INSTALLED_APPS, REST_FRAMEWORK

DEBUG = env_bool("DEBUG", True)
SECRET_KEY = env_str("SECRET_KEY", "dev-only-insecure-key-do-not-use-in-production")

# `.app.github.dev` is the domain of forwarded ports in GitHub Codespaces.
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", ["localhost", "127.0.0.1", ".app.github.dev"])
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    ["http://localhost:5173", "http://127.0.0.1:5173", "https://*.app.github.dev"],
)

# In GitHub Codespaces the app is opened through a forwarded HTTPS address, so links in
# emails must point there instead of localhost.
_codespace = os.environ.get("CODESPACE_NAME")
if _codespace and FRONTEND_URL in ("http://localhost:5173", "http://127.0.0.1:5173"):
    _domain = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
    FRONTEND_URL = f"https://{_codespace}-5173.{_domain}"

ALLOW_DEMO_SEED = env_bool("ALLOW_DEMO_SEED", True)
EMAIL_LOG_TO_CONSOLE = True

# API schema and interactive docs: /api/schema/ and /api/docs/ (development only).
INSTALLED_APPS = [*INSTALLED_APPS, "drf_spectacular"]
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}
SPECTACULAR_SETTINGS = {
    "TITLE": "FabriSee API",
    "DESCRIPTION": "Client management system for commercial display projects.",
    "VERSION": "0.2.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
