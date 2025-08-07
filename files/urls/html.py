from django.urls import path

from ..views.html import generate_link, public_download, delete_file

app_name = "files_html"

urlpatterns = [
    path("share/<uuid:file_id>/", generate_link, name="generate_link"),
    path("share/<uuid:token>/view/", public_download, name="public_download"),
    path("delete/<uuid:file_id>/", delete_file, name="delete_file"),
]
