from datetime import timedelta
from storages.backends.s3boto3 import S3Boto3Storage

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST

from apps.core.utils.request import is_ajax
from .mixins import SharedLinkLookupMixin, SharedLinkPresignMixin
from .models import UploadedFile, SharedLink


class GenerateLinkView(LoginRequiredMixin, View):
    """
    Create or retrieve an active public link for a user's uploaded file.
    """

    http_method_names = ["post"]
    
    def post(self, request, file_id):
        file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
        link, _created = SharedLink.objects.get_or_create_active(
            file=file,
            ttl=timedelta(minutes=5),
            now=timezone.now()
        )

        share_url = request.build_absolute_uri(
            reverse("files:share_page", args=[link.token])
        )
        return render(request, "files/link_created.html", {
            "share_url": share_url,
            "expiry_ts": int(link.expires_at.timestamp()),
            "server_now_ts": int(timezone.now().timestamp()),
        })
    

@method_decorator(require_POST, name="dispatch")
class DeleteFileView(LoginRequiredMixin, View):
    """
    Deletes a user-owned file (POST only). 

    AJAX returns 204 on success or 404 if missing; 
    non-AJAX redirects with a flash message.
    """

    def post(self, request, file_id):
        obj = UploadedFile.objects.filter(id=file_id, user=request.user).first()

        if not obj:
            if is_ajax(request):
                return HttpResponse(status=404)
            messages.error(request, "File not found or not owned by you.")
            return redirect("core:dashboard")

        obj.delete()
        if is_ajax(request):
            return HttpResponse(status=204)
        messages.success(request, "File deleted.")
        return redirect("core:dashboard")
    

class PublicDownloadView(SharedLinkLookupMixin, View):
    """
    Renders the public download page for a shared link.

    Shows an 'expired' page with HTTP 410 if the link is no longer valid.
    """

    http_method_names = ["get"]
    template_name = "files/public_download.html"

    def get(self, request, token):
        link = self.get_link(token)

        if link.is_expired():
            resp = render(request, "files/link_expired.html", status=410)
            resp["Cache-Control"] = "no-store"  # prevent caching
            return resp
        
        # Render the download page with file info + expiry timestamp
        context = {
            "file": link.file,
            "expiry_ts": int(link.expires_at.timestamp()),
            "token": token,  # used for download redirect URL
        }
        resp = render(request, self.template_name, context)
        resp["Cache-Control"] = "no-store"
        return resp


class PublicDownloadRedirectView(SharedLinkLookupMixin, 
                                 SharedLinkPresignMixin,
                                 View):
    """
    Redirects to a presigned S3 URL for a shared file.

    Shows an 'expired' page with HTTP 410 if the link is no longer valid.
    """
    
    http_method_names = ["get", "head"]

    def get(self, request, token, *args, **kwargs):
        link = self.get_link(token)

        if link.is_expired():
            return render(request, "files/link_expired.html", status=410)
        
        uploaded = link.file

        # S3-specific kwargs for presigning
        url_kwargs = {}
        if isinstance(default_storage, S3Boto3Storage):
            url_kwargs = {
                "expire": self.expires_in_seconds(link),
                "parameters": self.response_headers(uploaded.filename)
            }

        url = default_storage.url(uploaded.file.name, **url_kwargs)
        return HttpResponseRedirect(url)

    def head(self, request, token, *args, **kwargs):
        """
        Same as `get()` but returns headers only (for HEAD requests).
        """
        return self.get(request, token, *args, **kwargs)
