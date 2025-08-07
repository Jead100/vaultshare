from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from files.models import UploadedFile
from files.forms import FileUploadForm


def home(request):
    return render(request, "core/home.html")


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

        files = UploadedFile.objects.filter(user=request.user)

        # Always return JSON for POST
        html = render_to_string("partials/_files_list.html", {"files": files})
        return JsonResponse({"success": True, "html": html, "count": files.count()})

    else:
        form = FileUploadForm()
        files = UploadedFile.objects.filter(user=request.user)
        return render(request, "core/dashboard.html", {"form": form, "files": files})
