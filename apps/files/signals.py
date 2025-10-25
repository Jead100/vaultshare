from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import UploadedFile

@receiver(post_delete, sender=UploadedFile)
def delete_file_from_storage_on_delete(sender, instance, **kwargs):
    f = getattr(instance, "file", None)
    if f and f.name:
        f.delete(save=False)
