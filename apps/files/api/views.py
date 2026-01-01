from datetime import timedelta

from django.core.files.storage import default_storage
from django.http import HttpResponseRedirect
from django.utils import timezone
from rest_framework import filters, permissions, status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.throttling import (
    AnonRateThrottle,
    ScopedRateThrottle,
    UserRateThrottle,
)
from rest_framework.viewsets import ModelViewSet
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


class SharedLinkMetaView(GenericAPIView):
    """
    API view for retrieving or revoking a shared link.

    Anyone may retrieve metadata if the link is not expired.
    Revoking requires authentication and ownership of the file.
    """

    serializer_class = SharedLinkMetaSerializer
    queryset = SharedLink.objects.select_related("file")
    lookup_field = "token"

    throttle_classes = [AnonRateThrottle, UserRateThrottle, ScopedRateThrottle]
    throttle_scope = "shares:meta"

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get(self, request, *args, **kwargs):
        """
        Return metadata for a link if not expired.
        """
        link = self.get_object()

        if link.is_expired():
            return Response({"detail": "Link expired."}, status=status.HTTP_410_GONE)

        serializer = self.get_serializer(link)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """
        Revoke the link by expiring it (owner only).
        """
        link = self.get_object()

        if link.file.user != request.user:
            return Response(
                {"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN
            )

        link.expires_at = timezone.now()
        link.save(update_fields=["expires_at"])
        return Response({"detail": "Share link revoked."}, status=status.HTTP_200_OK)


class SharedLinkDownloadView(SharedLinkPresignMixin, GenericAPIView):
    """
    API view for downloading a shared file via a presigned S3 URL.
    """

    permission_classes = [permissions.AllowAny]
    queryset = SharedLink.objects.select_related("file")
    lookup_field = "token"

    throttle_classes = [AnonRateThrottle, UserRateThrottle, ScopedRateThrottle]
    throttle_scope = "shares:download"

    def get(self, request, *args, **kwargs):
        """
        Validate the token & expiry, then redirect to a short-lived S3 URL.
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

    def head(self, request, *args, **kwargs):
        """
        Same as `get()` but returns headers only (for HEAD requests).
        """
        return self.get(request, *args, **kwargs)
