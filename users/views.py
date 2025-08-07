from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from .forms import CustomUserCreationForm


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("core:dashboard")
    else:
        form = CustomUserCreationForm()
    return render(request, "users/registration/register.html", {"form": form})


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("home")
