import os

from django.urls import reverse

from rest_framework import serializers

from .models import UploadedFile, SharedLink

class BaseUploadedFileSerializer(serializers.ModelSerializer):
    """
    Base serializer for uploaded files.

    - Exposes `id`, `filename`, `size`, `file`, `uploaded_at`.
    - `file` and `filename` are writable by default.
    """

    class Meta:
        model = UploadedFile
        fields = ["id", "filename", "size", "file", "uploaded_at"]
        read_only_fields = ["id", "size", "uploaded_at"]


class UploadedFileCreateSerializer(BaseUploadedFileSerializer):
    """
    Serializer for creating uploads.

    - `file` is required.  
    - `filename` is optional; if given, the uploaded extension is enforced.  
    - `size` and `user` are populated.
    """

    class Meta(BaseUploadedFileSerializer.Meta):
        extra_kwargs = {
            "file": {"required": True},
            "filename": {"required": False}
        }
    
    def create(self, validated_data):
        file = validated_data["file"]
        custom_name = validated_data.get("filename")

        if custom_name:
            # Enforce the uploaded file's extension
            _, original_ext = os.path.splitext(os.path.basename(file.name))
            validated_data["filename"] = f"{custom_name}{original_ext}"
        else:
            validated_data["filename"] = os.path.basename(file.name)

        validated_data["size"] = file.size
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class UploadedFileReadUpdateSerializer(BaseUploadedFileSerializer):
    """
    Serializer for reading and updating uploads.

    - Makes `file` read-only.  
    - Allows renaming `filename`; preserves the stored extension.
    """

    class Meta(BaseUploadedFileSerializer.Meta):
        extra_kwargs = {
            "file":{"read_only": True},
            "filename": {"required": False}
        }
    
    def update(self, instance, validated_data):
        new_name = validated_data.get("filename")
        if new_name:
            # Preserve stored extension
            _, original_ext = os.path.splitext(os.path.basename(instance.file.name))
            validated_data["filename"] = f"{new_name}{original_ext}"
        return super().update(instance, validated_data)


class SharedLinkSerializer(serializers.ModelSerializer):
    """
    
    """

    share_link = serializers.SerializerMethodField()

    class Meta:
        model = SharedLink
        fields = ["share_link", "expires_at"]
        read_only_fields = fields

    def get_share_link(self, obj):
        request = self.context["request"]  # retrieve from view
        return request.build_absolute_uri(
            reverse("files_api:share_meta", args=[str(obj.token)])
        )
    

class SharedLinkMetaSerializer(serializers.ModelSerializer):
    """
    Public metadata for a shared link (read-only).

    Includes filename/size/expiry state and both 
    an API direct download endpoint and an HTML download page.
    """

    filename = serializers.CharField(source="file.filename", read_only=True)
    size = serializers.IntegerField(source="file.size", read_only=True)
    download_api = serializers.SerializerMethodField()
    download_page = serializers.SerializerMethodField()

    class Meta(SharedLinkSerializer.Meta):
        model = SharedLink
        fields = ["filename", "size", "expires_at", 
                  "download_api", "download_page"]
        read_only_fields = fields

    def get_download_api(self, obj):
        request = self.context["request"]
        return request.build_absolute_uri(
            reverse("files_api:share_download", args=[str(obj.token)])
        )

    def get_download_page(self, obj):
        request = self.context["request"]
        return request.build_absolute_uri(
            reverse("files_html:public_download", args=[str(obj.token)])
        )
