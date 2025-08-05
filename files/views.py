from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import UploadedFile, SharedLink
from .serializers import UploadedFileSerializer, SharedLinkSerializer


class UploadedFileViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UploadedFileSerializer

    def get_queryset(self):
        return UploadedFile.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post"])
    def share(self, request, pk=None):
        """ 
        Generate an expiring link for public access.
        """
        file = self.get_object()
        expires_in = int(request.data.get("expires_in", 60))  # seconds
        expires_at = timezone.now() + timedelta(seconds=expires_in)
        link = SharedLink.objects.create(file=file, expires_at=expires_at)
        return Response(
            SharedLinkSerializer(link).data,
            status=status.HTTP_201_CREATED
        )

@login_required
def generate_link(request, file_id):
    file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    expires_at = timezone.now() + timedelta(minutes=5)  # default expiry
    link = SharedLink.objects.create(file=file, expires_at=expires_at)
    return render(request, "files/link_created.html", {"link": link})

def public_download(request, token):
    shared_link = get_object_or_404(SharedLink, token=token)
    if shared_link.is_expired():
        return render(request, "files/link_expired.html")
    return render(request, "files/public_download.html", {"file": shared_link.file})
