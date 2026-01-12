from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import filters, permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import UnsupportedMediaType
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ...models import SharedLink, UploadedFile
from ..openapi import file_id_param
from ..pagination import FilePagination
from ..serializers import (
    SharedLinkSerializer,
    ShareTTLSerializer,
    UploadedFileCreateSerializer,
    UploadedFileReadUpdateSerializer,
)


@extend_schema(tags=["Files"])
@extend_schema_view(
    # OpenAPI schema for default CRUD actions is defined here;
    # custom actions are documented at the method level.
    list=extend_schema(
        summary="List uploaded files",
        description=(
            "Returns a paginated list of files owned by the authenticated user."
        ),
    ),
    retrieve=extend_schema(
        summary="Retrieve a file",
        description=(
            "Returns metadata for a single file owned by the authenticated user."
        ),
        parameters=[file_id_param],
    ),
    create=extend_schema(
        summary="Upload a new file",
        description="Uploads a new file and returns its metadata.",
    ),
    update=extend_schema(exclude=True),
    partial_update=extend_schema(
        summary="Update file metadata",
        description=(
            "Partially updates file metadata (e.g., filename) for a file owned "
            "by the authenticated user."
        ),
        parameters=[file_id_param],
    ),
    destroy=extend_schema(
        summary="Delete a file",
        description="Permanently deletes a file owned by the authenticated user.",
        parameters=[file_id_param],
    ),
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
        if self.action == "create":
            return UploadedFileCreateSerializer
        if self.action in {"share", "share_regenerate"}:
            return SharedLinkSerializer
        return UploadedFileReadUpdateSerializer

    def _get_share_ttl(self):
        # Validate and return the requested share TTL (seconds)
        ttl = ShareTTLSerializer(data=self.request.data)
        ttl.is_valid(raise_exception=True)
        return ttl.validated_data["expires_in"]

    def create(self, request, *args, **kwargs):
        """
        Override default `create` to enforce multipart/form-data uploads.
        """
        ct = (request.content_type or "").lower()
        if not ct.startswith("multipart/form-data"):
            raise UnsupportedMediaType(
                request.content_type, detail="Uploads must use multipart/form-data"
            )
        return super().create(request, *args, **kwargs)

    # File sharing actions

    @extend_schema(
        summary="Create or return a share link",
        description=(
            "Creates (or returns) a share link for a file.\n\n"
            "Optionally accepts `expires_in` (seconds). If omitted, a default TTL is used."
        ),
        parameters=[file_id_param],
        request=ShareTTLSerializer,
        responses={200: SharedLinkSerializer, 201: SharedLinkSerializer},
    )
    @action(detail=True, methods=["post"], url_path="share")
    def share(self, request, pk=None):
        """
        Create or return an active share link for the file.

        Optionally accepts `expires_in` (seconds) to control link expiration.
        """
        file = self.get_object()
        expires_in = self._get_share_ttl()

        # Either reuse the active link or create one with the requested expiry
        link, created = SharedLink.objects.get_or_create_active(
            file=file, ttl=timedelta(seconds=expires_in)
        )

        serializer = self.get_serializer(link, context={"request": request})
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Revoke the share link",
        description="Revokes the share link for a file (if any).",
        parameters=[file_id_param],
        request=None,
        responses={
            200: inline_serializer(
                name="ShareDeleteResponse",
                fields={
                    "detail": serializers.CharField(),
                    "revoked": serializers.IntegerField(),
                },
            ),
        },
    )
    @share.mapping.delete
    def share_delete(self, request, pk=None):
        """
        Revoke the active share link by expiring it.
        """
        file = self.get_object()

        # Revoke any active link
        now = timezone.now()
        revoked = (
            SharedLink.objects.active(now).filter(file=file).update(expires_at=now)
        )

        detail = "Link revoked." if revoked else "No active link to revoke."
        return Response(
            {"detail": detail, "revoked": revoked}, status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Regenerate the share link",
        description=(
            "Regenerates the share token for a file, invalidating the previous link.\n\n"
            "Optionally accepts `expires_in` (seconds)."
        ),
        parameters=[file_id_param],
        request=ShareTTLSerializer,
        responses={201: SharedLinkSerializer},
    )
    @action(detail=True, methods=["post"], url_path="share/regenerate")
    def share_regenerate(self, request, pk=None):
        """
        Regenerate the share link for the file, expiring any existing one.

        Optionally accepts `expires_in` (seconds) to control link expiration.
        """
        file = self.get_object()

        # Expire any active link now
        now = timezone.now()
        SharedLink.objects.active(now).filter(file=file).update(expires_at=now)

        # Create a fresh one
        expires_in = self._get_share_ttl()

        new_link = SharedLink.objects.create(
            file=file, expires_at=now + timedelta(seconds=expires_in)
        )

        serializer = self.get_serializer(new_link, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
