import tempfile

import pytest
from rest_framework.test import APIClient

from .factories import UserFactory


@pytest.fixture
def api_client():
    """
    Return an unauthenticated API client.
    """
    return APIClient()


@pytest.fixture
def user():
    """
    Create and return a test user.
    """
    return UserFactory()


@pytest.fixture
def auth_client():
    """
    Factory for an authenticated API client.

    Call with a user to authenticate as that user, or with no arguments
    to authenticate as a new test user.
    """

    def _make(user=None):
        if user is None:
            user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return _make


@pytest.fixture
def authed_client(auth_client, user):
    """
    Return an API client authenticated as the default test user.
    """
    return auth_client(user)


@pytest.fixture(autouse=True)
def _temp_media(settings):
    """
    Isolate MEDIA_ROOT so file I/O stays inside a temp dir during tests.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        settings.MEDIA_ROOT = tmpdir
        yield
        # files auto-removed with tmpdir context
