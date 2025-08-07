from django.urls import path

from . import views

app_name = "files_html"

urlpatterns = [
    path("share/<uuid:file_id>/", views.generate_link, name="generate_link"),
    path("share/<uuid:token>/view/", views.public_download, name="public_download"),
    path("delete/<uuid:file_id>/", views.delete_file, name="delete_file"),
]
