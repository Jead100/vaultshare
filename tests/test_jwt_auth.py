import pytest
from django.apps import apps
from django.conf import settings
from django.test.utils import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from .factories import PASSWORD
from .url_helpers import (
    files_list_url,
    jwt_obtain_pair_url,
    jwt_refresh_url,
    jwt_verify_url,
)

# Helpers


def _auth_type():
    """
    First configured auth header type (default 'Bearer').
    """
    return settings.SIMPLE_JWT.get("AUTH_HEADER_TYPES", ("Bearer",))[0]


def _obtain_pair(client: APIClient, email: str, password: str) -> dict:
    """
    POST to token_obtain_pair and return token payload as dict.
    """
    resp = client.post(jwt_obtain_pair_url(), {"email": email, "password": password})
    assert resp.status_code == status.HTTP_200_OK, resp.content
    data = resp.json()
    assert "access" in data and "refresh" in data
    return data


# Tests


@pytest.mark.django_db
def test_obtain_pair_and_access_protected_view(api_client, user):
    tokens = _obtain_pair(api_client, email=user.email, password=PASSWORD)
    api_client.credentials(HTTP_AUTHORIZATION=f"{_auth_type()} {tokens['access']}")
    resp = api_client.get(files_list_url())
    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_refresh_rotation_and_blacklist(api_client, user):
    """
    When ROTATE_REFRESH_TOKENS=True and BLACKLIST_AFTER_ROTATION=True, the old
    refresh token should be rejected after a rotation.
    """
    if not apps.is_installed("rest_framework_simplejwt.token_blacklist"):
        pytest.skip("rest_framework_simplejwt.token_blacklist not installed")

    with override_settings(
        SIMPLE_JWT={
            **settings.SIMPLE_JWT,
            "ROTATE_REFRESH_TOKENS": True,
            "BLACKLIST_AFTER_ROTATION": True,
        }
    ):
        tokens = _obtain_pair(api_client, email=user.email, password=PASSWORD)
        r1 = tokens["refresh"]

        # First refresh returns a new refresh token
        r_resp = api_client.post(jwt_refresh_url(), {"refresh": r1})
        assert r_resp.status_code == status.HTTP_200_OK
        r2 = r_resp.json()["refresh"]
        assert r1 != r2  # rotation happened

        # The old refresh is now blacklisted
        r_old = api_client.post(jwt_refresh_url(), {"refresh": r1})
        assert r_old.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_tampered_access_token_fails_verification(api_client, user):
    tokens = _obtain_pair(api_client, email=user.email, password=PASSWORD)
    valid = tokens["access"]

    # Tamper with the valid access token (flip the last char)
    tampered = valid[:-1] + ("A" if valid[-1] != "A" else "B")

    # Verify tampered token fails
    resp = api_client.post(jwt_verify_url(), {"token": tampered})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    body = resp.json()
    assert body.get("code") in {
        "token_not_valid",
        "token_invalid",
        "authorization_header_missing",
    }


@pytest.mark.django_db
def test_expired_access_token_is_rejected(api_client, user):
    """
    Expired access tokens should be rejected (even considering SIMPLE_JWT['LEEWAY']).
    """
    import jwt

    tokens = _obtain_pair(api_client, email=user.email, password=PASSWORD)

    # Decode the valid access token
    algo = settings.SIMPLE_JWT["ALGORITHM"]
    secret = settings.SECRET_KEY
    decoded = jwt.decode(tokens["access"], secret, algorithms=[algo])

    # Modify exp to be in the past, accounting for leeway
    leeway = settings.SIMPLE_JWT["LEEWAY"]
    decoded["exp"] = decoded["iat"] - leeway - 1

    # Re-encode the expired token
    expired = jwt.encode(decoded, secret, algorithm=algo)

    # Attempt to access protected view with expired token
    api_client.credentials(HTTP_AUTHORIZATION=f"{_auth_type()} {expired}")
    resp = api_client.get(files_list_url())
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_garbage_refresh_token_returns_401(api_client):
    resp = api_client.post(jwt_refresh_url(), {"refresh": "totally-not-a-jwt"})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
