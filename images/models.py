# models.py

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.sessions.models import Session
from django.conf import settings
import glob
import os


def session_directory_path(instance, filename): 
    return os.path.join('session', str(instance.session_key), filename)
    #return '/session/{0}/{1}'.format(instance.session_key, filename)

def sample_directory_path(instance, filename): 
    return os.path.join('session', str(instance.session_key), 'sample', filename)

def identity_directory_path(instance, filename): 
    return os.path.join('session', str(instance.session_key), 'identity',filename)

def clut_directory_path(instance, filename): 
    return os.path.join('session', str(instance.session_key), 'clut', filename)

def get_film_choices():
    names = ["Color"]
    files = ["1"]
    files += glob.glob(os.path.join(os.getcwd(), settings.CLUT_DIR, "Color/*.png"), recursive=True)
    names += [os.path.basename(str(file[:-4])) for file in glob.glob(os.path.join(os.getcwd(), settings.CLUT_DIR, "Color/*.png"), recursive=True)]
    files += ["2"]
    names += ["Black and White"]
    files += glob.glob(os.path.join(os.getcwd(), settings.CLUT_DIR, "Black and White/*.png"), recursive=True)
    names += [os.path.basename(str(file[:-4])) for file in glob.glob(os.path.join(os.getcwd(), settings.CLUT_DIR, "Black_and_White/*.png"), recursive=True)]
    file_map = dict(zip(files,names))
    print(len(file_map.keys()))
    return file_map

def validate_film_choice(value):
    if not isinstance(value, str):
        raise ValidationError("This field must be a string of characters.")
    
    if value in ("Color", "Black and White"):
        raise ValidationError(f"{value} is not an film. It is just there to seperate Color from Black and White.") #redirect back to create page

class ImageUpload(models.Model):
    name = models.CharField(max_length=200)
    session_key = models.ForeignKey(Session, on_delete=models.SET_NULL, blank=True, null=True)
    image = models.ImageField(upload_to=session_directory_path)
    filtered = models.ImageField(upload_to=session_directory_path, default=None) #TODO change these to file fields
    film = models.CharField(max_length=200, choices=get_film_choices, validators=[validate_film_choice], blank=False, null=False, default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        
        return f'{self.name}'

class CLUTUpload(models.Model):
    image = models.ImageField(upload_to='CLUT/user_uploads/')
    created_at = models.DateTimeField(auto_now_add=True)
    film = models.CharField(max_length=200, blank=False, null=False, default=None)
    exposure = models.FloatField()
    info = models.CharField(max_length=200)

    def __str__(self):
        return f'{self.film} {self.exposure}'

class CLUTCreate(models.Model):
    session_key = models.ForeignKey(Session, on_delete=models.SET_NULL, blank=True, null=True)
    clut = models.ImageField(upload_to=clut_directory_path, blank=True, null=True)
    sample = models.ImageField(upload_to=sample_directory_path, default=None)
    identity = models.ImageField(upload_to=identity_directory_path, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    info = models.CharField(max_length=200)

    def __str__(self):
        return f'{self.created_at}'