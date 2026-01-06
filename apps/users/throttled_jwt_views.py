from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# Subclassed SimpleJWT views with scoped throttling applied.


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_scope = "auth:token"


class ThrottledTokenRefreshView(TokenRefreshView):
    throttle_scope = "auth:refresh"


class ThrottledTokenVerifyView(TokenVerifyView):
    throttle_scope = "auth:verify"
