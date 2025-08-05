from rest_framework import serializers

from .models import UploadedFile, SharedLink


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ["id", "filename", "size", "file", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at", "filename", "size"]

    def create(self, validated_data):
        file = validated_data["file"]
        validated_data["filename"] = file.name
        validated_data["size"] = file.size
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
    

class SharedLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedLink
        fields = ["token", "expires_at"]
