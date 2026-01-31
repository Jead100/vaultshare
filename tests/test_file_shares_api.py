import pytest
from rest_framework import status

from .factories import UploadedFileFactory
from .url_helpers import files_share_regenerate_url, files_share_url

# UploadedFileViewSet @action: POST /files/{id}/share/


@pytest.mark.django_db
def test_share_create_first_then_reuse(authed_client, user):
    """
    Returns 201 on new share; 200 on reuse of an active link.
    """
    f = UploadedFileFactory(user=user)

    resp1 = authed_client.post(
        files_share_url(f.id), {"expires_in": 120}, format="json"
    )
    assert resp1.status_code == status.HTTP_201_CREATED
    token1 = resp1.data["token"]

    resp2 = authed_client.post(
        files_share_url(f.id), {"expires_in": 120}, format="json"
    )
    assert resp2.status_code == status.HTTP_200_OK
    assert resp2.data["token"] == token1  # reused


@pytest.mark.django_db
def test_share_create_invalid_expires_in(authed_client, user):
    """
    Returns 400 with validation error for invalid expires_in.
    """
    f = UploadedFileFactory(user=user)
    resp = authed_client.post(files_share_url(f.id), {"expires_in": 0}, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "expires_in" in resp.data


# UploadedFileViewSet @action: DELETE /files/{id}/share/


@pytest.mark.django_db
def test_share_delete_revokes(authed_client, user):
    """
    Returns 200 and reports revoked count when an active link is revoked.
    """
    f = UploadedFileFactory(user=user)
    url = files_share_url(f.id)

    authed_client.post(url, {"expires_in": 60}, format="json")

    resp = authed_client.delete(url)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {"detail": "Link revoked.", "revoked": 1}


@pytest.mark.django_db
def test_share_delete_when_none_active(authed_client, user):
    """
    Returns 200 and revoked=0 when there is no active link to revoke.
    """
    f = UploadedFileFactory(user=user)

    resp = authed_client.delete(files_share_url(f.id))
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {"detail": "No active link to revoke.", "revoked": 0}


# UploadedFileViewSet @action: POST /files/{id}/share/regenerate/


@pytest.mark.django_db
def test_share_regenerate_expires_old_and_creates_new(authed_client, user):
    """
    Returns 201 after expiring the old link and creating a new one.
    """
    f = UploadedFileFactory(user=user)

    resp1 = authed_client.post(
        files_share_url(f.id), {"expires_in": 120}, format="json"
    )
    assert resp1.status_code == status.HTTP_201_CREATED
    old_token = resp1.data["token"]

    resp2 = authed_client.post(
        files_share_regenerate_url(f.id), {"expires_in": 120}, format="json"
    )
    assert resp2.status_code == status.HTTP_201_CREATED
    assert resp2.data["token"] != old_token
