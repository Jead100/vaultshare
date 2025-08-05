from django.urls import path

from .. import views

urlpatterns = [
    path("share/<uuid:file_id>/", views.generate_link, name="generate_link"),
    path("share/<uuid:token>/view/", views.public_download, name="public_download"),
]
