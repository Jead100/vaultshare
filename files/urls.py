from django.urls import path

from files.views import tailwind_home

urlpatterns = [
    path("", view=tailwind_home, name="tailwind-home"),
]
