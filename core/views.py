from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect

from files.models import UploadedFile
from files.forms import FileUploadForm


@login_required
def dashboard(request):
    if request.method == "POST":
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.save(commit=False)
            uploaded_file.user = request.user
            uploaded_file.filename = uploaded_file.file.name
            uploaded_file.size = uploaded_file.file.size
            uploaded_file.save()
            return redirect("dashboard")
    else:
        form = FileUploadForm()

    files = UploadedFile.objects.filter(user=request.user)
    return render(request, "core/dashboard.html", {"form": form, "files": files})


def login_placeholder(request):
    return HttpResponse("Login page coming soon.")


def logout_placeholder(request):
    return HttpResponse("Logout page coming soon.")


def register_placeholder(request):
    return HttpResponse("Register page coming soon.")
