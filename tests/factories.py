from datetime import timedelta

import factory
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.files.models import SharedLink, UploadedFile

User = get_user_model()

PASSWORD = "pass123!"


class UserFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating User instances with a known password for tests.
    """

    class Meta:
        model = User
        skip_postgeneration_save = True  # we use create_user

    email = factory.sequence(lambda n: f"user{n}@example.com")
    password = PASSWORD  # plaintext; user manager hashes it

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Use the model's manager to create users
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)


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
