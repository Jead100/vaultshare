from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from core.views import home


urlpatterns = [
    path("admin/", admin.site.urls),

    # HTML routes (public → private)
    path("", home, name="home"),  # landing page
    path("dashboard/", include(("core.urls_html", "core_html"), namespace="core_html")),
    path("auth/", include(("users.urls_html", "users_html"), namespace="users_html")),
    path("files/", include(("files.urls_html", "files_html"), namespace="files_html")),

    # API routes
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/files/", include(("files.urls_api", "files_api"), namespace="files_api")),
]


# Dev tools
if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]

# Media
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
