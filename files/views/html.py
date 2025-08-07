from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import UploadedFile, SharedLink


@login_required
def generate_link(request, file_id):
    file = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    # Check for existing, non-expired link
    link = SharedLink.objects.filter(file=file, expires_at__gt=timezone.now()).first()

    # If no valid link, create a new one
    if not link:
        expires_at = timezone.now() + timedelta(minutes=5)
        link = SharedLink.objects.create(file=file, expires_at=expires_at)

    share_url = request.build_absolute_uri(
        reverse("files_html:public_download", args=[link.token])
    )

    return render(request, "files/link_created.html", {
        "share_url": share_url,
        "expires_at": link.expires_at.isoformat(),
    })


@login_required
@require_POST
def delete_file(request, file_id):
    try:
        UploadedFile.objects.get(id=file_id, user=request.user).delete()
        success = True
    except UploadedFile.DoesNotExist:
        success = False

    files = UploadedFile.objects.filter(user=request.user)
    html = render_to_string("partials/_files_list.html", {"files": files})
    return JsonResponse({"success": success, "html": html, "count": files.count()})


def public_download(request, token):
    shared_link = get_object_or_404(SharedLink, token=token)
    if shared_link.is_expired():
        return render(request, "files/link_expired.html")
    return render(request, "files/public_download.html", {"file": shared_link.file})
