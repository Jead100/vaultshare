from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core.views import HomeView
from apps.users.throttled_jwt_views import (
    ThrottledTokenObtainPairView,
    ThrottledTokenRefreshView,
    ThrottledTokenVerifyView,
)

urlpatterns = [
    # --- UI routes ---
    path("", HomeView.as_view(), name="home"),  # landing page
    path("dashboard/", include("apps.core.urls", namespace="core")),
    path("auth/", include("apps.users.urls", namespace="users")),
    path("files/", include("apps.files.urls", namespace="files")),
    # --- API routes ---
    # auth (SimpleJWT) #
    path(
        "api/v1/auth/token/",
        ThrottledTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/v1/auth/token/refresh/",
        ThrottledTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "api/v1/auth/token/verify/",
        ThrottledTokenVerifyView.as_view(),
        name="token_verify",
    ),
    # files #
    path("api/v1/", include("apps.files.api.urls", namespace="files_api")),
    path("api/v1/session-auth/", include("rest_framework.urls")),
]

# Optionally expose the Django admin interface
if settings.EXPOSE_ADMIN:
    urlpatterns += [
        path("admin/", admin.site.urls),
    ]

# Dev-only live reload support
if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]

# Serve uploaded media locally in development when not using S3
if settings.DEBUG and not settings.USE_S3:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
