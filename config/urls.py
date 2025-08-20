from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from core.views import HomeView


urlpatterns = [
    path("admin/", admin.site.urls),

    # HTML routes (public → private)
    path("", HomeView.as_view(), name="home"),  # landing page
    path("dashboard/", include(("core.urls", "core"), namespace="core")),
    path("auth/", include(("users.urls", "users"), namespace="users")),
    path("files/", include(("files.urls.html", "files_html"), namespace="files_html")),

    # API routes
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/files/", include(("files.urls.api", "files_api"), namespace="files_api")),
]


# Dev tools
if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]

# Media
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
