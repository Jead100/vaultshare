from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from apps.core.views import HomeView
from apps.users.jwt_views import EmailTokenObtainPairView


urlpatterns = [
    path("admin/", admin.site.urls),

    ### UI routes ###
    path("", HomeView.as_view(), name="home"),  # landing page
    path("dashboard/", include(("apps.core.urls", "core"), namespace="core")),
    path("auth/", include(("apps.users.urls", "users"), namespace="users")),
    path("files/", include(("apps.files.urls", "files"), namespace="files")),

    ### API routes ###
    # Files
    path("api/v1/", include(("apps.files.api.urls", "files_api"), namespace="files_api")),

    # JWT auth
    path("api/v1/auth/token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    path('api/v1/session-auth/', include('rest_framework.urls')),
]

# Dev-only routes
if settings.DEBUG:
    # Live reload support (django-browser-reload)
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
    # Serve media locally
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
