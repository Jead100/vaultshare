from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import SharedLink


class Command(BaseCommand):
    help = "Delete all expired shared links."

    def handle(self, *args, **kwargs):
        deleted, _ = SharedLink.objects.filter(expires_at__lt=timezone.now()).delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted} expired shared links.")
        )
