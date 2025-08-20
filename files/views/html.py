from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.utils.request import is_ajax
from ..models import UploadedFile, SharedLink


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
            reverse("files_html:public_download", args=[link.token])
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
    
    
class PublicDownloadView(TemplateView):
    """
    Public file download page from a shared link token.
    """

    template_name = "files/public_download.html"

    def get(self, request, token, *args, **kwargs):
        shared_link = get_object_or_404(SharedLink, token=token)
        if shared_link.is_expired():
            return render(request, "files/link_expired.html")
        return render(request, self.template_name, {"file": shared_link.file})
