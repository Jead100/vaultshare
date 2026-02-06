from django.core.files.storage import default_storage
from django.http import HttpResponseRedirect
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from storages.backends.s3boto3 import S3Boto3Storage

from ...mixins import SharedLinkPresignMixin
from ...models import SharedLink
from ..openapi import detail_message_resp, share_token_param
from ..serializers import SharedLinkMetaSerializer


@extend_schema(tags=["Shares"])
@extend_schema_view(
    retrieve=extend_schema(
        summary="Retrieve shared link metadata",
        description=(
            "Returns public metadata for a shared link token if it is still valid.\n\n"
            "If the link is expired, returns 410 Gone."
        ),
        parameters=[share_token_param],
        responses={
            200: SharedLinkMetaSerializer,
            410: OpenApiResponse(
                response=detail_message_resp,
                description="Link expired.",
            ),
        },
    ),
    destroy=extend_schema(
        summary="Revoke a shared link",
        description=(
            "Revokes a shared link by expiring it.\n\n"
            "Requires authentication and ownership of the underlying file."
        ),
        parameters=[share_token_param],
        responses={
            200: OpenApiResponse(
                response=detail_message_resp,
                description="Share link revoked.",
            ),
            403: OpenApiResponse(
                response=detail_message_resp,
                description="Not allowed.",
            ),
        },
    ),
    download=extend_schema(
        summary="Download a shared file",
        description=(
            "Redirects to a short-lived storage URL for downloading the shared file.\n\n"
            "Returns an HTTP 302 redirect. If the link is expired, returns 410 Gone.\n\n"
            "Note: Some clients may not follow cross-origin redirects; open the URL "
            "directly in a browser to download the file."
        ),
        parameters=[share_token_param],
        responses={
            302: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="Redirect to the storage URL (Location header).",
            ),
            410: OpenApiResponse(
                response=detail_message_resp,
                description="Link expired.",
            ),
        },
    ),
)
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

        if link.is_expired:
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

        if link.is_expired:
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
