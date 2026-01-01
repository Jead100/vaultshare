from django.contrib import admin

from .models import SharedLink, UploadedFile

admin.site.register(UploadedFile)
admin.site.register(SharedLink)
