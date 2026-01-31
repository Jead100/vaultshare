import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status

from .factories import UploadedFileFactory
from .url_helpers import files_detail_url, files_list_url


# Helper
def _unwrap_list(data):
    """
    Return the list payload from an API response.

    Supports three response shapes:
    - A raw list
    - A dict with a top-level "results" key (paginated)
    - A dict with a top-level "data" wrapper
    """
    payload = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(payload, dict):
        return payload.get("results", payload)
    return payload


# Tests


@pytest.mark.django_db
def test_upload_file(authed_client):
    f = SimpleUploadedFile("test.txt", b"Hello world", content_type="text/plain")
    resp = authed_client.post(files_list_url(), {"file": f}, format="multipart")

    assert resp.status_code == status.HTTP_201_CREATED
    assert "filename" in resp.data
    assert resp.data["filename"].endswith("test.txt")


@pytest.mark.django_db
def test_upload_rejects_non_multipart_with_custom_error(authed_client):
    resp = authed_client.post(
        files_list_url(), {"file": "not-a-real-upload"}, format="json"
    )

    assert resp.status_code == 415
    assert "must use multipart/form-data" in resp.json()["detail"]


@pytest.mark.django_db
def test_list_shows_only_own_files(authed_client, user):
    """
    List endpoint should include only files owned by the authenticated user.
    """
    # Create files for the authenticated user and for someone else
    mine = [UploadedFileFactory(user=user) for _ in range(3)]
    other = [UploadedFileFactory() for _ in range(2)]

    resp = authed_client.get(files_list_url(page_size=10))
    assert resp.status_code == status.HTTP_200_OK

    # Unwrap {"data": ...} and/or {"results": ...} if payload is paginated
    payload = _unwrap_list(resp.data)
    objs = payload if isinstance(payload, list) else payload.get("results", payload)

    # Normalize all IDs to strings (API returns str; model uses UUID)
    ids = {str(obj["id"]) for obj in objs}
    mine_ids = {str(f.id) for f in mine}
    other_ids = {str(f.id) for f in other}

    # All mine are present; none of the others are present
    assert mine_ids.issubset(ids)
    assert ids.isdisjoint(other_ids)


@pytest.mark.django_db
def test_retrieve_own_file_ok(authed_client, user):
    f = UploadedFileFactory(user=user)
    resp = authed_client.get(files_detail_url(f.id))
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["id"] == str(f.id)


@pytest.mark.django_db
def test_retrieve_other_users_file_404(authed_client):
    f = UploadedFileFactory()  # different owner
    resp = authed_client.get(files_detail_url(f.id))
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_rename_filename(authed_client, user):
    f = UploadedFileFactory(user=user)
    resp = authed_client.patch(
        files_detail_url(f.id), {"filename": "newname"}, format="json"
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["filename"].startswith("newname")


@pytest.mark.django_db
def test_rename_filename_rejects_blank(authed_client, user):
    f = UploadedFileFactory(user=user)
    resp = authed_client.patch(files_detail_url(f.id), {"filename": ""}, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_delete_file_removes_from_storage(authed_client, user):
    f = UploadedFileFactory(user=user)
    name = f.file.name
    storage = f.file.storage or default_storage

    assert storage.exists(name)  # precondition

    resp = authed_client.delete(files_detail_url(f.id))
    assert resp.status_code in (status.HTTP_204_NO_CONTENT, status.HTTP_200_OK)
    assert not storage.exists(name)  # file should be gone from storage
