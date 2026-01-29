"""
Helpers for enforcing per-user storage quotas on uploads.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Sum

from .models import UploadedFile


def get_user_storage_used_bytes(user) -> int:
    """
    Return the total storage used by a user in bytes, excluding expired uploads.
    """
    agg = UploadedFile.objects.filter(user=user).active().aggregate(total=Sum("size"))
    return int(agg["total"] or 0)


def enforce_user_quota(user, incoming_size: int) -> None:
    """
    Raise ValidationError if adding a file of the given size would exceed
    the user's configured storage quota.
    """
    cap = getattr(settings, "MAX_USER_STORAGE_BYTES", None)
    if not cap:
        return

    used = get_user_storage_used_bytes(user)
    if used + incoming_size > cap:
        cap_mb = cap / (1024 * 1024)
        raise ValidationError(
            f"Storage quota exceeded. Max total storage is {cap_mb:g} MB."
        )
