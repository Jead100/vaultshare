import pytest
import tempfile
from rest_framework.test import APIClient

from .factories import UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture(autouse=True)
def _temp_media(settings):
    """
    Isolate MEDIA_ROOT so file I/O stays inside a temp dir during tests.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        settings.MEDIA_ROOT = tmpdir
        yield
        # files auto-removed with tmpdir context
