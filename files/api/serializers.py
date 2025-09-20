import os
import re

from django.urls import reverse

from rest_framework import serializers

from ..models import UploadedFile, SharedLink


INVALID_CHARS_RE = re.compile(r'[\\/:*?"<>|]')

class BaseUploadedFileSerializer(serializers.ModelSerializer):
    """
    Base serializer for uploaded files.

    - Exposes `id`, `filename`, `size`, `file`, `uploaded_at`.
    - `file` and `filename` are writable by default.
    """
    
    filename = serializers.CharField(
        required=False,
        allow_blank=False,
        trim_whitespace=True,
        max_length=255
    )

    class Meta:
        model = UploadedFile
        fields = ["id", "filename", "size", "file", "uploaded_at"]
        read_only_fields = ["id", "size", "uploaded_at"]
    
    # Simple file name validation methods:
    
    def validate_filename(self, value):
        base = os.path.basename(value)
        if INVALID_CHARS_RE.search(base):
            raise serializers.ValidationError(
                r'Filename cannot contain any of: \ / : * ? " < > |'
            )
        return base

    def enforce_filename_uniqueness(self, user, filename: str, exclude_pk=None) -> None:
        duplicate_name = (
            UploadedFile.objects
            .filter(user=user, filename=filename)
            .exclude(pk=exclude_pk)  # exclude self.instance, if it exists
            .exists()
        )
        if duplicate_name:
            raise serializers.ValidationError(
                {"filename": "You already have a file with this name."}
            )


class UploadedFileCreateSerializer(BaseUploadedFileSerializer):
    """
    Serializer for creating uploads.

    - `file` is required.  
    - `filename` is optional; if given, the uploaded extension is enforced.  
    """

    class Meta(BaseUploadedFileSerializer.Meta):
        extra_kwargs = {
            "file": {"required": True},
            "filename": {"required": False}
        }
    
    def create(self, validated_data):
        file = validated_data["file"]
        user = self.context["request"].user

        custom_name = validated_data.get("filename")
        if custom_name:
            # Enforce the original uploaded file's extension
            _, original_ext = os.path.splitext(os.path.basename(file.name))
            final_name = f"{custom_name}{original_ext}"
        else:
            # Use uploaded name (basename) as-is
            final_name = os.path.basename(file.name)

        self.enforce_filename_uniqueness(user, final_name)

        validated_data["filename"] = final_name
        validated_data["size"] = file.size
        validated_data["user"] = user
        return super().create(validated_data)


class UploadedFileReadUpdateSerializer(BaseUploadedFileSerializer):
    """
    Serializer for reading and updating uploads.

    - `file` is read-only.  
    - Allows renaming `filename`; preserves the stored extension.
    """

    class Meta(BaseUploadedFileSerializer.Meta):
        extra_kwargs = {"file":{"read_only": True}}
    
    def update(self, instance, validated_data):
        new_name = validated_data.get("filename")
        if new_name:
            # Preserve the stored extension from the current filename
            _, original_ext = os.path.splitext(instance.filename)
            final_name = f"{new_name}{original_ext}"

            user = self.context["request"].user
            self.enforce_filename_uniqueness(user, final_name, exclude_pk=instance.pk)

            validated_data["filename"] = final_name
            
        return super().update(instance, validated_data)


class SharedLinkSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for shared links.

    - Exposes: `token`, `created_at`, `expires_at`, and `share_link`.
    - `share_link` is the absolute URL (built from the token) to the metadata
      endpoint, which provides minimal file details and direct download links.
    """

    share_link = serializers.SerializerMethodField()

    class Meta:
        model = SharedLink
        fields = ["token", "share_link", "created_at", "expires_at",]
        read_only_fields = fields

    def get_share_link(self, obj):
        # Return the absolute URL to the share metadata endpoint for this token
        request = self.context["request"]
        return request.build_absolute_uri(
            reverse("files_api:share_meta", args=[str(obj.token)])
        )


class SharedLinkMetaSerializer(serializers.ModelSerializer):
    """
    Public metadata for a shared link (read-only).

    Includes filename/size/expiry state and both 
    an API download URL (`download_api`) and an 
    HTML download page ULR(`download_page`)
    """

    filename = serializers.CharField(source="file.filename", read_only=True)
    size = serializers.IntegerField(source="file.size", read_only=True)
    download_api = serializers.SerializerMethodField()
    download_page = serializers.SerializerMethodField()

    class Meta(SharedLinkSerializer.Meta):
        model = SharedLink
        fields = ["filename", "size", "download_api", 
                  "download_page", "expires_at",]
        read_only_fields = fields

    def get_download_api(self, obj):
        request = self.context["request"]
        return request.build_absolute_uri(
            reverse("files_api:share_download", args=[str(obj.token)])
        )

    def get_download_page(self, obj):
        request = self.context["request"]
        return request.build_absolute_uri(
            reverse("files:share_page", args=[str(obj.token)])
        )
