import os

from django import forms

from .models import UploadedFile


class FileUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ["file"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def save(self, commit=True):
        inst = super().save(commit=False)
        inst.user = self.user
        inst.filename = os.path.basename(inst.file.name)
        inst.size = inst.file.size
        if commit:
            inst.save()
        return inst
