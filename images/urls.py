from django.urls import path
from . import views
from pathlib import Path
from django.http import HttpResponse

urlpatterns = [
    path('images/<str:session_key>/', views.display_images, name='key_uploads'),
    path('images/', views.display_images, name='session_uploads'),
    path('', views.upload_image,  name='images_create'),
    path('donate/', views.donate, name='donate'),
    path('about/', views.about, name='about'),
    path('clut/', views.clut, name='clut'),
    #path('images/<str:session_key>/delete/<str:image_name>/', views.delete_image, name='delete_image'),
]
