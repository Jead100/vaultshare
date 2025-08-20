from django.urls import path

from ..views.html import GenerateLinkView, DeleteFileView, PublicDownloadView

app_name = "files_html"

urlpatterns = [
    path("share/<uuid:file_id>/", GenerateLinkView.as_view(), name="generate_link"),
    path("share/<uuid:token>/view/", PublicDownloadView.as_view(), name="public_download"),
    path("delete/<uuid:file_id>/", DeleteFileView.as_view(), name="delete_file"),
]
