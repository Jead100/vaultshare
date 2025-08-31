from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from core.views import HomeView
from users.jwt_views import EmailTokenObtainPairView


urlpatterns = [
    path("admin/", admin.site.urls),

    # HTML pages
    # ----------
    path("", HomeView.as_view(), name="home"),  # landing page
    path("dashboard/", include(("core.urls", "core"), namespace="core")),
    path("auth/", include(("users.urls", "users"), namespace="users")),
    path("files/", include(("files.urls.html", "files_html"), namespace="files_html")),

    # API routes
    # ----------
    # Files
    path("api/v1/", include(("files.urls.api", "files_api"), namespace="files_api")),

    # JWT
    path("api/v1/auth/token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    path('api/v1/session-auth/', include('rest_framework.urls')),
]

# Development-only routes
if settings.DEBUG:
    # Live reload support (django-browser-reload)
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
    # Serve user-uploaded media files during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
