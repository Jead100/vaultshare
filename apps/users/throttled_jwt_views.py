"""
Subclassed SimpleJWT views with scoped throttling applied.
"""

from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


@extend_schema(
    tags=["Authentication"],
    summary="Obtain access and refresh tokens",
)
class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_scope = "auth:token"


@extend_schema(
    tags=["Authentication"],
    summary="Refresh an access token",
)
class ThrottledTokenRefreshView(TokenRefreshView):
    throttle_scope = "auth:refresh"


@extend_schema(
    tags=["Authentication"],
    summary="Verify a token",
)
class ThrottledTokenVerifyView(TokenVerifyView):
    throttle_scope = "auth:verify"
