from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import SharedLinkDownloadView, SharedLinkMetaView, UploadedFileViewSet

app_name = "files_api"

router = DefaultRouter()
router.register(r"files", UploadedFileViewSet, basename="files")

urlpatterns = router.urls + [
    path("shares/<uuid:token>/", SharedLinkMetaView.as_view(), name="share_meta"),
    path(
        "shares/<uuid:token>/download/",
        SharedLinkDownloadView.as_view(),
        name="share_download",
    ),
]
