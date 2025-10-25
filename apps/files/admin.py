from django.contrib import admin

from .models import UploadedFile, SharedLink


admin.site.register(UploadedFile)
admin.site.register(SharedLink)
