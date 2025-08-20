import uuid

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class SharedLinkQuerySet(models.QuerySet):
    """
    Query helper for SharedLink, e.g., active (non-expired) links.
    """
    def active(self, now=None):
        now = now or timezone.now()
        return self.filter(expires_at__gt=now)


class SharedLinkManager(models.Manager):
    """
    Manager with helpers for retrieving or creating active links.
    """
    def get_queryset(self):
        return SharedLinkQuerySet(self.model, using=self._db)
    
    def get_or_create_active(self, file, ttl=timedelta(minutes=5), now=None):
        """
        Returns an existing active link for the file or creates a new one. 
        """
        now = now or timezone.now()
        link = self.get_queryset().active(now).filter(file=file).first()
        if link:
            return link, False
        
        return self.create(file=file, expires_at=now + ttl), True


class UploadedFile(models.Model):
    """
    A file uploaded by a user.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to="uploads/%Y/%m/%d/")
    filename = models.CharField(max_length=255)
    size = models.PositiveIntegerField()  # in bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} ({self.user.email})"


class SharedLink(models.Model):
    """
    Temporary public link to access an uploaded file. 

    Includes a custom manager/queryset for active link retrieval and creation.
    """

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    file = models.ForeignKey(to=UploadedFile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    objects = SharedLinkManager()

    def is_expired(self):
        return timezone.now() > self.expires_at
