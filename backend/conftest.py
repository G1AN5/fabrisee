import pytest
from django.core.cache import cache
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def _isolated_media_root(settings, tmp_path):
    """Uploads written by a test go to a temporary directory, never to backend/media."""
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture(autouse=True)
def _clear_cache():
    """Throttle counters live in the cache; start every test with an empty one."""
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def login(api_client):
    """`login(user)` signs `user` in on the shared API client and returns the client."""

    def _login(user):
        api_client.force_authenticate(user=None)
        api_client.force_login(user)
        return api_client

    return _login
