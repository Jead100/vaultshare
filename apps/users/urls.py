from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import EmailLoginForm
from .views import SignUpView

app_name = "users"

urlpatterns = [
    path("register/", SignUpView.as_view(), name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="users/registration/login.html",
            authentication_form=EmailLoginForm,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
