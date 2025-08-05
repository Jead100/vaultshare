from rest_framework.routers import DefaultRouter

from ..views import UploadedFileViewSet

router = DefaultRouter()
router.register("files", UploadedFileViewSet, basename="files")

urlpatterns = router.urls
