from datetime import timedelta

import factory
from django.utils import timezone

from tests.factories import UserFactory

from ..models import SharedLink, UploadedFile


class UploadedFileFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating UploadedFile instances with a test file.
    """

    class Meta:
        model = UploadedFile
        skip_postgeneration_save = True

    user = factory.SubFactory(UserFactory)
    file = factory.django.FileField(
        filename=factory.sequence(lambda n: f"test_{n}.txt"),
        data=b"hello world",
    )

    @factory.lazy_attribute
    def filename(self):
        return self.file.name

    @factory.lazy_attribute
    def size(self):
        return self.file.size


class SharedLinkFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating SharedLink instances with a default expiry.
    """

    class Meta:
        model = SharedLink
        skip_postgeneration_save = True

    file = factory.SubFactory(UploadedFileFactory)
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(minutes=5))
