"""Settings shared by every environment.

Environment-specific modules (dev.py, test.py, prod.py) import everything from here and
adjust it. Values come from environment variables; see `.env.example` in the repository root.
"""

from pathlib import Path

import dj_database_url

from config.env import env_bool, env_int, env_list, env_str

# backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# repository root
REPO_DIR = BASE_DIR.parent

SECRET_KEY = env_str("SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS: list[str] = env_list("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS: list[str] = env_list("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "apps.core",
    "apps.clients",
    "apps.accounts",
    "apps.projects",
    "apps.quotations",
    "apps.designs",
    "apps.notifications",
    "apps.activity",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database -------------------------------------------------------------------------
# SQLite by default (a file in backend/data/). Setting DATABASE_URL to a PostgreSQL URL
# switches the database without code changes, so keep all queries inside the Django ORM.
DEFAULT_SQLITE_PATH = BASE_DIR / "data" / "fabrisee.sqlite3"


def build_database_config(url: str) -> dict:
    """Turn a DATABASE_URL into a Django database configuration."""
    config = dj_database_url.parse(url, conn_max_age=60)
    if config["ENGINE"] == "django.db.backends.sqlite3":
        name = str(config["NAME"])
        if name and name != ":memory:" and not Path(name).is_absolute():
            # Relative SQLite paths are relative to the repository root, whatever the
            # current directory is (for example `sqlite:///backend/data/fabrisee.sqlite3`).
            config["NAME"] = str(REPO_DIR / name)
        config["CONN_MAX_AGE"] = 0
        config["OPTIONS"] = {
            # WAL lets readers work while the scheduler or another request writes.
            "init_command": "PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;",
            # Take the write lock at BEGIN so concurrent writers wait instead of failing.
            "transaction_mode": "IMMEDIATE",
        }
    return config


DATABASES = {
    "default": build_database_config(env_str("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")),
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Authentication -------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
# The React app reads the csrftoken cookie and sends it back in the X-CSRFToken header.
CSRF_COOKIE_HTTPONLY = False

# --- Internationalization -------------------------------------------------------------
LANGUAGE_CODE = "en"
TIME_ZONE = env_str("TIME_ZONE", "Asia/Manila")
USE_I18N = True
USE_TZ = True

# --- Static files and uploads ---------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Uploaded files live on local disk and are served only through permission-checked API
# views (apps.projects.views.FileDownloadView); MEDIA_URL is never routed.
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "media/"
# The production build of the React app (served by Django in production).
FRONTEND_DIST_DIR = REPO_DIR / "frontend" / "dist"
# Keep uploads on disk rather than in memory above 2.5 MB (Django default) and allow the
# largest configurable upload (SystemSetting.max_upload_mb, hard ceiling below).
MAX_UPLOAD_MB_CEILING = 50
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# --- Django REST Framework ------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.accounts.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "login": "10/min",
        "password_reset": "5/min",
    },
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

# --- Email ----------------------------------------------------------------------------
# Development: every message is stored in EmailLog (and printed to the console).
# Production: set EMAIL_BACKEND to Django's SMTP backend and fill in the EMAIL_* values.
EMAIL_BACKEND = env_str("EMAIL_BACKEND", "apps.notifications.backends.DatabaseEmailBackend")
EMAIL_HOST = env_str("EMAIL_HOST", "localhost")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = env_str("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env_str("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = env_str("DEFAULT_FROM_EMAIL", "FabriSee <no-reply@fabrisee.local>")
# Print each logged email to the console (development convenience).
EMAIL_LOG_TO_CONSOLE = False

# --- FabriSee -------------------------------------------------------------------------
# Base URL of the React app, used for links in emails.
FRONTEND_URL = env_str("FRONTEND_URL", "http://localhost:5173").rstrip("/")
# How often run_scheduler calls the reminder service (PR6).
REMINDER_CHECK_MINUTES = env_int("REMINDER_CHECK_MINUTES", 5)
# seed_demo and reset_demo refuse to run unless this is on. Must be off in production.
ALLOW_DEMO_SEED = env_bool("ALLOW_DEMO_SEED", False)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "loggers": {
        "apps": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
