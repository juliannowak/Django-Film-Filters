# models.py

from django.db import models
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from django.contrib.sessions.models import Session
from django.conf import settings
import glob
import os
import uuid
import posixpath
from django.core.cache import cache

def _uses_s3():
    backend = settings.STORAGES["default"]["BACKEND"]
    return backend == "storages.backends.s3boto3.S3Boto3Storage"

def _media_upload_path(relative_path):
    # Local FileSystemStorage already roots uploads at MEDIA_ROOT.
    # S3 storage is rooted at the bucket, so add the MEDIA_ROOT key prefix.
    if _uses_s3():
        return posixpath.join(str(settings.MEDIA_ROOT).strip("/"), relative_path)
    return relative_path

def _list_storage_files(directory):
    directories, files = default_storage.listdir(directory)

    for filename in files:
        yield posixpath.join(directory, filename)

    for dirname in directories:
        yield from _list_storage_files(posixpath.join(directory, dirname))

FILM_CHOICES_CACHE_KEY = "images:film_choices:v1"
FILM_CHOICES_CACHE_SECONDS = 0 #indefinitely

def _load_film_choices():
    choices = {"1": "Color", "2": "Black and White"}

    if _uses_s3():
        root = str(settings.CLUT_DIR).strip("/")
        files = _list_storage_files(root)
        relative_files = (key[len(root):].lstrip("/") for key in files)
    else:
        root = str(settings.CLUT_DIR)
        local_files = glob.glob(
            os.path.join(root, "**", "*.png"),
            recursive=True,
        )
        relative_files = (
            os.path.relpath(path, root).replace(os.sep, "/")
            for path in local_files
        )

    for relative_path in relative_files:
        if relative_path.lower().endswith(".png"):
            choices[relative_path] = os.path.splitext(
                posixpath.basename(relative_path)
            )[0]

    return choices

def get_film_choices():
    return cache.get_or_set(
        FILM_CHOICES_CACHE_KEY,
        _load_film_choices,
        timeout=FILM_CHOICES_CACHE_SECONDS,
    )

def image_directory_path(instance, filename):
    short_id = str(instance.short_id).replace("-", "")[:8]
    path = posixpath.join(
        "session", str(instance.session_key), "images", short_id, filename
    )
    return _media_upload_path(path)

def uploaded_clut_directory_path(instance, filename):
    short_id = str(instance.short_id).replace("-", "")[:8]
    path = posixpath.join(
        "session", str(instance.session_key), "cluts", short_id,
        "user_uploads", filename,
    )
    return _media_upload_path(path)

def sample_directory_path(instance, filename):
    short_id = str(instance.short_id).replace("-", "")[:8]
    path = posixpath.join(
        "session", str(instance.session_key), "generated", short_id,
        "samples", filename,
    )
    return _media_upload_path(path)

def identity_directory_path(instance, filename):
    short_id = str(instance.short_id).replace("-", "")[:8]
    path = posixpath.join(
        "session", str(instance.session_key), "generated", short_id,
        "identities", filename,
    )
    return _media_upload_path(path)

def clut_directory_path(instance, filename):
    short_id = str(instance.short_id).replace("-", "")[:8]
    path = posixpath.join(
        "session", str(instance.session_key), "generated", short_id,
        "cluts", filename,
    )
    return _media_upload_path(path)

def validate_film_choice(value):
    if not isinstance(value, str):
        raise ValidationError("This field must be a string of characters.")

    if value in ("Color", "Black and White"):
        # redirect back to create page
        raise ValidationError(
            f"{value} is not an film. It is just there to seperate Color from Black and White.")
# models for uploaded images and cluts TODO remove name or short_id, only one needed
class ImageUpload(models.Model):
    short_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    session_key = models.CharField(
        max_length=40, db_index=True, null=True, blank=True)
    # session_key = models.ForeignKey(Session, on_delete=models.SET_NULL, blank=True, null=True)
    image = models.ImageField(upload_to=image_directory_path)
    # TODO maybe make this not nullable, but make sure to process the file before saving the model instance and display a loading spinner while the file is being processed.
    filtered = models.ImageField(upload_to=image_directory_path, default=None, blank=True, null=True)
    film = models.CharField(max_length=200, choices=get_film_choices, validators=[
                            validate_film_choice], blank=False, null=False, default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        return f'{self.name}'

class CLUTUpload(models.Model):
    short_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True)
    session_key = models.ForeignKey(
        Session, on_delete=models.SET_NULL, blank=True, null=True)
    image = models.ImageField(
        upload_to=uploaded_clut_directory_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    film = models.CharField(max_length=200, blank=False,
                            null=False, default=None)
    exposure = models.SmallIntegerField()
    info = models.CharField(max_length=200)

    def __str__(self):
        return f'{self.film} {self.exposure}'

# models for generated cluts, samples, and identities
class CLUTCreator(models.Model):
    short_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True)
    session_key = models.CharField(
        max_length=40, db_index=True, null=True, blank=True)
    clut = models.ImageField(
        upload_to=clut_directory_path, blank=True, null=True)
    sample = models.ImageField(upload_to=sample_directory_path, default=None)
    identity = models.ImageField(
        upload_to=identity_directory_path, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.created_at}'
