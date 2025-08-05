import pytest

from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.test import APIClient

from users.models import User


@pytest.mark.django_db
def test_upload_file():
    user = User.objects.create_user(email="test@example.com", password="pass")
    client = APIClient()
    client.force_authenticate(user=user)

    file = SimpleUploadedFile("test.txt", b"Hello world", content_type="text/plain")
    response = client.post("/api/files/", {"file":file}, format="multipart")

    assert response.status_code == 201
    assert "filename" in response.data
