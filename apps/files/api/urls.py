from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter

from .views import SharedLinkViewSet, UploadedFileViewSet

app_name = "files_api"

router = DefaultRouter() if settings.DEBUG else SimpleRouter()
router.register(r"files", UploadedFileViewSet, basename="files")
router.register(r"shares", SharedLinkViewSet, basename="shares")

urlpatterns = [path("", include(router.urls))]
