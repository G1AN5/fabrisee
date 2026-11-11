"""Test settings: in-memory SQLite, fast password hashing, no console noise."""

from .base import *  # noqa: F403
from .base import build_database_config

DEBUG = False
SECRET_KEY = "test-only-secret-key"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
CSRF_TRUSTED_ORIGINS = []

DATABASES = {"default": build_database_config("sqlite://:memory:")}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "apps.notifications.backends.DatabaseEmailBackend"
EMAIL_LOG_TO_CONSOLE = False
DEFAULT_FROM_EMAIL = "FabriSee <no-reply@fabrisee.local>"
FRONTEND_URL = "http://localhost:5173"
TIME_ZONE = "Asia/Manila"
ALLOW_DEMO_SEED = True
REMINDER_CHECK_MINUTES = 5
