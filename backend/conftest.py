import pytest
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def _isolated_media_root(settings, tmp_path):
    """Uploads written by a test go to a temporary directory, never to backend/media."""
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def api_client():
    return APIClient()
