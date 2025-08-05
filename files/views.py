from datetime import timedelta

from django.utils import timezone

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

