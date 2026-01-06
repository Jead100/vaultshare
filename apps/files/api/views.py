from datetime import timedelta

from django.core.files.storage import default_storage
from django.http import HttpResponseRedirect
from django.utils import timezone
from rest_framework import filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from storages.backends.s3boto3 import S3Boto3Storage

from ..mixins import SharedLinkPresignMixin
from ..models import SharedLink, UploadedFile
from .pagination import FilePagination
from .serializers import (
    SharedLinkMetaSerializer,
    SharedLinkSerializer,
    UploadedFileCreateSerializer,
    UploadedFileReadUpdateSerializer,
)


class UploadedFileViewSet(ModelViewSet):
    """
    Viewset for managing user-uploaded files.

    Supports listing, uploading, retrieving, renaming filenames, and deleting.
    Includes extra actions for creating, revoking, and regenerating share links.
    """

    permission_classes = [permissions.IsAuthenticated]

    # Filters
    filter_backends = [filters.OrderingFilter]
    ordering = ["-uploaded_at", "-id"]  # default ordering
    ordering_fields = ["uploaded_at", "filename", "size"]
    pagination_class = FilePagination

    def get_queryset(self):
        # Restrict files to those owned by the current user
        return UploadedFile.objects.filter(user=self.request.user)

    def get_throttles(self):
        # Limit request rates per action
        if self.action == "create":
            self.throttle_scope = "files:upload"
        elif self.action == "share":
            self.throttle_scope = "files:share"
        elif self.action == "share_regenerate":
            self.throttle_scope = "files:share_regenerate"
        return super().get_throttles()

    def get_serializer_class(self):
        return (
            UploadedFileCreateSerializer
            if self.action == "create"
            else UploadedFileReadUpdateSerializer
        )

    @action(detail=True, methods=["post", "delete"], url_path="share")
    def share(self, request, pk=None):
        """
        Manage the share link for a file.

        - POST: Create or return the active share link (optional `expires_in`).
        - DELETE: Revoke the active share link.
        """
        file = self.get_object()

        if request.method == "DELETE":
            # Revoke any active link
            now = timezone.now()
            revoked = (
                SharedLink.objects.active(now).filter(file=file).update(expires_at=now)
            )

            if revoked == 0:
                return Response(
                    {"detail": "No active link exists. Nothing revoked."},
                    status=status.HTTP_200_OK,
                )

            return Response(
                {"detail": "Link revoked.", "revoked": revoked},
                status=status.HTTP_200_OK,
            )

        # POST:
        try:
            expires_in = int(request.data.get("expires_in", 300))
            if expires_in <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"expires_in": ["Must be a positive integer (seconds)."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Either reuse the active link or create one with the requested expiry
        link, created = SharedLink.objects.get_or_create_active(
            file=file, ttl=timedelta(seconds=expires_in)
        )

        serializer = SharedLinkSerializer(link, context={"request": request})
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="share/regenerate")
    def share_regenerate(self, request, pk=None):
        """
        Force-generate a new token, expiring any current active link.
        """
        file = self.get_object()

        # Expire any active link now
        now = timezone.now()
        SharedLink.objects.active(now).filter(file=file).update(expires_at=now)

        # Create a fresh one
        expires_in = int(request.data.get("expires_in", 300))
        new_link = SharedLink.objects.create(
            file=file, expires_at=now + timedelta(seconds=expires_in)
        )

        serializer = SharedLinkSerializer(new_link, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SharedLinkViewSet(SharedLinkPresignMixin, GenericViewSet):
    """
    Viewset for interacting with shared file links.

    - Anyone may retrieve metadata while the link is valid.
    - Revocation requires authentication and ownership of the file.
    - Includes an extra action for downloading the shared file via
      a short-lived storage URL.
    """

    queryset = SharedLink.objects.select_related("file")
    serializer_class = SharedLinkMetaSerializer
    lookup_field = "token"

    def get_permissions(self):
        if self.action == "destroy":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_throttles(self):
        if self.action == "destroy":
            self.throttle_scope = "shares:revoke"
        elif self.action == "download":
            self.throttle_scope = "shares:download"
        else:
            self.throttle_scope = "shares:meta"
        return super().get_throttles()

    def retrieve(self, request, *args, **kwargs):
        """
        Return public metadata for a shared link if it is still valid.
        """
        link = self.get_object()

        if link.is_expired():
            return Response({"detail": "Link expired."}, status=status.HTTP_410_GONE)

        serializer = self.get_serializer(link)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Revoke a shared link by expiring it (owner only).
        """
        link = self.get_object()

        if link.file.user != request.user:
            return Response(
                {"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN
            )

        link.expires_at = timezone.now()
        link.save(update_fields=["expires_at"])
        return Response({"detail": "Share link revoked."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, *args, **kwargs):
        """
        Redirect to a short-lived storage URL for downloading the shared file.
        """
        link = self.get_object()

        if link.is_expired():
            return Response({"detail": "Link expired."}, status=status.HTTP_410_GONE)

        uploaded = link.file

        # S3-specific kwargs for presigning
        url_kwargs = {}
        if isinstance(default_storage, S3Boto3Storage):
            url_kwargs = {
                "expire": self.expires_in_seconds(link),
                "parameters": self.response_headers(uploaded.filename),
            }

        url = default_storage.url(uploaded.file.name, **url_kwargs)
        return HttpResponseRedirect(url)

    @download.mapping.head
    def download_head(self, request, *args, **kwargs):
        """
        Handle HEAD requests for the download endpoint.

        Mirrors GET behavior while allowing clients to probe link validity
        without downloading the file.
        """
        return self.download(request, *args, **kwargs)
