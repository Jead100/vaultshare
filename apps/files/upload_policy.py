import os
from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ValidationError


@dataclass(frozen=True)
class UploadPolicy:
    allow_any: bool
    max_size: int
    allowed_exts: set[str]
    allowed_mime_types: set[str]


def get_upload_policy() -> UploadPolicy:
    return UploadPolicy(
        allow_any=getattr(settings, "ALLOW_ANY_FILE_TYPE", False),
        max_size=getattr(settings, "MAX_UPLOAD_SIZE", 25 * 1024 * 1024),
        allowed_exts=set(getattr(settings, "ALLOWED_UPLOAD_EXTENSIONS", set())),
        allowed_mime_types=set(getattr(settings, "ALLOWED_UPLOAD_MIME_TYPES", set())),
    )


def validate_uploaded_file(
    file_obj,
    *,
    filename: str | None = None,
    content_type: str | None = None,
) -> None:
    """
    Validate an uploaded file against the active upload policy.

    Enforces allowed extensions, best-effort MIME type consistency,
    and maximum file size. Raises ValidationError on failure.
    """

    policy = get_upload_policy()
    if policy.allow_any:
        return

    # Extension check
    name = filename or getattr(file_obj, "name", "") or ""
    _, ext = os.path.splitext(os.path.basename(name))
    ext = ext.lower()

    if policy.allowed_exts and ext not in policy.allowed_exts:
        allowed = ", ".join(sorted(policy.allowed_exts))
        raise ValidationError(f"Unsupported file type. Allowed extensions: {allowed}.")

    # MIME check (best-effort)
    if content_type:
        ct = content_type.split(";")[0].strip().lower()
        if policy.allowed_mime_types and ct not in policy.allowed_mime_types:
            raise ValidationError("Unsupported file content type.")

    # Size check
    size = getattr(file_obj, "size", None)
    if size is not None and size > policy.max_size:
        mb = policy.max_size / (1024 * 1024)
        raise ValidationError(f"File too large. Max size is {mb:g} MB.")
