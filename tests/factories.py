import factory
from django.contrib.auth import get_user_model

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
