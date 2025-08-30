from django.urls import path
from django.contrib.auth import views as auth_views

from .views import SignUpView
from .forms import EmailAuthenticationForm

app_name = "users"

urlpatterns = [
    path("register/", SignUpView.as_view(), name="register"),
    path("login/", auth_views.LoginView.as_view(
        template_name="users/registration/login.html",
        authentication_form=EmailAuthenticationForm
    ), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
