import os

from django import forms

from .models import UploadedFile
from .quota import enforce_user_quota
from .ttl import compute_expires_at
from .upload_policy import validate_uploaded_file


class FileUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ["file"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_file(self):
        f = self.cleaned_data.get("file")
        if f:
            # Enforce the configured upload policy (extension, MIME, size)
            validate_uploaded_file(
                f,
                filename=f.name,
                content_type=getattr(f, "content_type", None),
            )
            # Enforce per-user storage quota
            enforce_user_quota(self.user, int(getattr(f, "size", 0) or 0))
        return f

    def save(self, commit=True):
        inst = super().save(commit=False)

        # Populate upload metadata and expiration
        inst.user = self.user
        inst.filename = os.path.basename(inst.file.name)
        inst.size = inst.file.size
        inst.expires_at = compute_expires_at()

        if commit:
            inst.save()
        return inst
