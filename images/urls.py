from django.urls import path
from . import views
from pathlib import Path
from django.http import HttpResponse

urlpatterns = [
    path('', views.create_upload,  name='images_create'),
    path('clut_create/', views.create_clut, name='clut_create'),
    path('images/<str:session_key>/', views.display_images, name='key_uploads'),
    path('images/', views.display_images, name='session_uploads'),
    path('clut/', views.clut, name='clut'),
    path('clut/<str:session_key>/', views.display_cluts, name='key_cluts'),
    path('images/<str:session_key>/delete/<str:image_name>/', views.delete_image, name='delete_image'),
    path('clut/<str:session_key>/delete/<str:image_name>/', views.delete_clut, name='delete_clut'),
    path('donate/', views.donate, name='donate'),
    path('about/', views.about, name='about'),

]
