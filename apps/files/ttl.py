from datetime import datetime

from django.conf import settings
from django.utils import timezone


def compute_expires_at(*, now: datetime | None = None) -> datetime | None:
    """
    Return the expiration timestamp for an uploaded file based on the
    configured TTL, or None if not configured.
    """
    ttl = getattr(settings, "DEFAULT_FILE_TTL_SECONDS", None)
    if not ttl:
        return None
    now = now or timezone.now()
    return now + timezone.timedelta(seconds=int(ttl))
