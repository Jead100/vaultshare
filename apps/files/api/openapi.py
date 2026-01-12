"""
Shared OpenAPI parameters and response serializers used across
multiple API view modules.
"""

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    inline_serializer,
)
from rest_framework import serializers

file_id_param = OpenApiParameter(
    name="id",
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.UUID,
    description="Unique identifier of the uploaded file.",
)

share_token_param = OpenApiParameter(
    name="token",
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.UUID,
    description="Share link token.",
)

detail_message_resp = inline_serializer(
    name="DetailMessageResponse",
    fields={
        "detail": serializers.CharField(),
    },
)
