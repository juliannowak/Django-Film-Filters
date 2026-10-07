# models.py

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.sessions.models import Session
from django.conf import settings
import glob
import os
import uuid

def get_film_choices():
    names = ["Color"]
    files = ["1"]
    files += glob.glob(os.path.join(os.getcwd(),
                       settings.CLUT_DIR, "Color/*.png"), recursive=True)
    names += [os.path.basename(str(file[:-4])) for file in glob.glob(
        os.path.join(os.getcwd(), settings.CLUT_DIR, "Color/*.png"), recursive=True)]
    files += ["2"]
    names += ["Black and White"]
    files += glob.glob(os.path.join(os.getcwd(), settings.CLUT_DIR,
                       "Black and White/*.png"), recursive=True)
    names += [os.path.basename(str(file[:-4])) for file in glob.glob(os.path.join(
        os.getcwd(), settings.CLUT_DIR, "Black_and_White/*.png"), recursive=True)]
    # TODO add user uploaded cluts to the list of choices too
    file_map = dict(zip(files, names))
    print(len(file_map.keys()))
    return file_map

def validate_film_choice(value):
    if not isinstance(value, str):
        raise ValidationError("This field must be a string of characters.")

    if value in ("Color", "Black and White"):
        # redirect back to create page
        raise ValidationError(
            f"{value} is not an film. It is just there to seperate Color from Black and White.")

# media file upload paths
def image_directory_path(instance, filename):
    short_id = str(instance.short_id).replace('-', '')[:8]
    return os.path.join('session', str(instance.session_key), 'images', short_id, filename)

def uploaded_clut_directory_path(instance, filename):
    short_id = str(instance.short_id).replace('-', '')[:8]
    return os.path.join('session', str(instance.session_key), 'cluts', short_id, 'user_uploads', filename)

# these are for generated cluts, samples, and identities
def sample_directory_path(instance, filename):
    short_id = str(instance.short_id).replace('-', '')[:8]
    return os.path.join('session', str(instance.session_key), 'generated', short_id, 'samples', filename)

def identity_directory_path(instance, filename):
    short_id = str(instance.short_id).replace('-', '')[:8]
    return os.path.join('session', str(instance.session_key), 'generated', short_id, 'identities', filename)

def clut_directory_path(instance, filename):
    short_id = str(instance.short_id).replace('-', '')[:8]
    return os.path.join('session', str(instance.session_key), 'generated', short_id, 'cluts', filename)

# models for uploaded images and cluts TODO remove name or short_id, only one needed
class ImageUpload(models.Model):
    short_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    session_key = models.CharField(
        max_length=40, db_index=True, null=True, blank=True)
    # session_key = models.ForeignKey(Session, on_delete=models.SET_NULL, blank=True, null=True)
    image = models.ImageField(upload_to=image_directory_path)
    # TODO change these to file fields
    filtered = models.ImageField(upload_to=image_directory_path, default=None)
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
