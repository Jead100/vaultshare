from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from apps.files.tests.factories import SharedLinkFactory, UploadedFileFactory

from .url_helpers import share_download_url, share_meta_url


@pytest.mark.django_db
def test_share_meta_allows_anonymous_when_valid(api_client):
    link = SharedLinkFactory()
    resp = api_client.get(share_meta_url(link.token))
    assert resp.status_code == status.HTTP_200_OK

    # Meta fields
    assert "filename" in resp.data
    assert "size" in resp.data
    assert "expires_at" in resp.data
    assert "download_api" in resp.data
    assert "download_page" in resp.data

    # Sanity checks on values
    assert resp.data["filename"] == link.file.filename
    assert resp.data["size"] == link.file.size

    # Meta links should be absolute URLs in tests
    assert resp.data["download_api"].startswith("http://testserver/")
    assert resp.data["download_page"].startswith("http://testserver/")


@pytest.mark.django_db
def test_share_meta_returns_410_when_expired(api_client):
    link = SharedLinkFactory(expires_at=timezone.now() - timedelta(seconds=1))
    resp = api_client.get(share_meta_url(link.token))
    assert resp.status_code == status.HTTP_410_GONE


@pytest.mark.django_db
def test_share_download_redirects_when_valid(api_client):
    link = SharedLinkFactory()
    uploaded = link.file

    resp = api_client.get(share_download_url(link.token))
    assert resp.status_code in (
        status.HTTP_302_FOUND,
        status.HTTP_301_MOVED_PERMANENTLY,
    )

    # Should redirect to storage URL for the underlying file.
    # Works for local storage and for S3-style URLs
    assert uploaded.file.name in resp["Location"]


@pytest.mark.django_db
def test_share_download_returns_410_when_expired(api_client):
    link = SharedLinkFactory(expires_at=timezone.now() - timedelta(seconds=1))
    resp = api_client.get(share_download_url(link.token))
    assert resp.status_code == status.HTTP_410_GONE


@pytest.mark.django_db
def test_share_download_head_mirrors_get(api_client):
    link = SharedLinkFactory()
    uploaded = link.file

    resp = api_client.head(share_download_url(link.token))
    assert resp.status_code in (
        status.HTTP_302_FOUND,
        status.HTTP_301_MOVED_PERMANENTLY,
    )
    assert uploaded.file.name in resp["Location"]


@pytest.mark.django_db
def test_share_revoke_requires_auth(api_client):
    link = SharedLinkFactory()
    resp = api_client.delete(share_meta_url(link.token))
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_share_revoke_forbidden_for_non_owner(auth_client):
    owner_file = UploadedFileFactory()
    link = SharedLinkFactory(file=owner_file)

    other_user_client = auth_client()  # new user
    resp = other_user_client.delete(share_meta_url(link.token))
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_share_revoke_owner_expires_link(authed_client, user):
    uploaded = UploadedFileFactory(user=user)
    link = SharedLinkFactory(file=uploaded)

    resp = authed_client.delete(share_meta_url(link.token))
    assert resp.status_code == status.HTTP_200_OK

    link.refresh_from_db()
    assert link.expires_at is not None
    assert link.is_expired is True
