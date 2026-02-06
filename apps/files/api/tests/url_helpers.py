from urllib.parse import urlencode

from django.urls import reverse


def files_list_url(**qs):
    """
    /api/v1/files/
    """
    url = reverse("files_api:files-list")
    return f"{url}?{urlencode(qs)}" if qs else url


def files_detail_url(file_id):
    """
    /api/v1/files/<id>/
    """
    return reverse("files_api:files-detail", kwargs={"pk": str(file_id)})


def files_share_url(file_id):
    """
    /api/v1/files/<id>/share/
    """
    return reverse("files_api:files-share", kwargs={"pk": str(file_id)})


def files_share_regenerate_url(file_id):
    """
    /api/v1/files/<id>/share/regenerate/
    """
    return reverse("files_api:files-share-regenerate", kwargs={"pk": str(file_id)})


def share_meta_url(token):
    """
    /api/v1/shares/<uuid:token>/
    """
    return reverse("files_api:shares-detail", kwargs={"token": str(token)})


def share_download_url(token):
    """
    /api/v1/shares/<uuid:token>/download/
    """
    return reverse("files_api:shares-download", kwargs={"token": str(token)})
