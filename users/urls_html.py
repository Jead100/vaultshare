from django.urls import path
from django.contrib.auth import views as auth_views

from .views import register, CustomLogoutView
from.forms import CustomAuthenticationForm

app_name = "users_html"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(
        template_name="users/registration/login.html",
        authentication_form=CustomAuthenticationForm
    ), name="login"),
    path("register/", register, name="register"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
]
