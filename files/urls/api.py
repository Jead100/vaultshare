from rest_framework.routers import DefaultRouter

from ..views.api import UploadedFileViewSet

app_name = "files_api"

router = DefaultRouter()
router.register(r"", UploadedFileViewSet, basename="files")

urlpatterns = router.urls
