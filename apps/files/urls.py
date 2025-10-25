from django.urls import path

from .views import (
    GenerateLinkView, DeleteFileView, 
    PublicDownloadView, PublicDownloadRedirectView
)

app_name = "files"

urlpatterns = [
    path("share/<uuid:file_id>/", GenerateLinkView.as_view(), name="generate_link"),
    path("share/<uuid:token>/view/", PublicDownloadView.as_view(), name="share_page"),
    path("share/<uuid:token>/download/", PublicDownloadRedirectView.as_view(), name="share_download"),
    path("delete/<uuid:file_id>/", DeleteFileView.as_view(), name="delete_file"),
]
