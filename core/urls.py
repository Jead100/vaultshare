from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_placeholder, name="login"),
    path("logout/", views.logout_placeholder, name="logout"),
    path("register/", views.register_placeholder, name="register"),
]
