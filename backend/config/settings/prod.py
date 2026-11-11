"""Production settings. Deployment itself is Milestone 10 (see the build guide, section 17)."""

from django.core.exceptions import ImproperlyConfigured

from config.env import env_bool

from .base import *  # noqa: F403
from .base import ALLOWED_HOSTS, FRONTEND_DIST_DIR, MIDDLEWARE, SECRET_KEY

DEBUG = False

if not SECRET_KEY or SECRET_KEY.startswith(("dev-only", "change-me")):
    raise ImproperlyConfigured("Set a strong SECRET_KEY environment variable in production.")
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("Set the ALLOWED_HOSTS environment variable in production.")

# Demo data must never be loaded into a production database.
ALLOW_DEMO_SEED = False

# HTTPS only.
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_CONTENT_TYPE_NOSNIFF = True

# WhiteNoise serves the collected static files, including the built React app.
MIDDLEWARE = [
    MIDDLEWARE[0],
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],
]
STATICFILES_DIRS = [FRONTEND_DIST_DIR] if FRONTEND_DIST_DIR.is_dir() else []
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
