"""
Mixins for SharedLink lookup and presigned URL generation for downloads.
"""

import mimetypes

from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import SharedLink


class SharedLinkLookupMixin:
    """
    Retrieve a SharedLink by token with the related file preloaded.
    """
    
    def get_link(self, token: str) -> SharedLink:
        return get_object_or_404(
            SharedLink.objects.select_related("file"),
            token=token
        )


class SharedLinkPresignMixin:
    """
    Generate expiry seconds and response headers for presigned URLs.
    """

    def expires_in_seconds(self, link: SharedLink) -> int:
        remaining = int((link.expires_at - timezone.now()).total_seconds())
        return max(1, remaining)
    
    def response_headers(self, filename: str) -> dict:
        ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        return {
            "ResponseContentType": ctype,
            "ResponseContentDisposition": f'attachment; filename="{filename}"',
        }
