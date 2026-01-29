import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import UploadedFile

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Delete expired uploads and their storage objects"

    def handle(self, *args, **options):
        qs = UploadedFile.objects.filter(
            expires_at__isnull=False,
            expires_at__lte=timezone.now(),
        )

        deleted = 0
        for pk in qs.values_list("pk", flat=True).iterator():
            try:
                count, _ = UploadedFile.objects.filter(pk=pk).delete()
                deleted += count
            except Exception:
                logger.exception("Failed deleting expired UploadedFile %s", pk)
                self.stderr.write(f"Failed deleting upload {pk}")

        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} expired uploads."))
