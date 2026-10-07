from django.urls import path
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView
from . import views
from pathlib import Path
from django.http import HttpResponse

urlpatterns = [
    path('', views.display_images, name='images'),
    path('images/<str:session_key>/', views.display_images, name='key_images'),
    # rename to session_images or images_by_session
    path('images/', views.display_images, name='session_uploads'),
    path('cluts/', views.display_cluts, name='cluts'),
    path('cluts/<str:session_key>/', views.display_cluts, name='key_cluts'),
    
    path('images/delete/<str:session_key>/<int:pk>/',
         views.delete_image_handler, name='delete_image'),
    path('images/delete/<str:session_key>/',
         views.delete_image_handler, name='delete_image'),
    path('cluts/delete/<str:session_key>/<int:pk>/',
         views.delete_clut_handler, name='delete_clut'),
     path('cluts/delete/<str:session_key>/',
         views.delete_clut_handler, name='delete_clut'),
    
    path('create/', views.upload_clut, name='create_clut'),
    path('donate/', views.donate, name='donate'),
    path('about/', views.about, name='about'),
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('images/favicon.ico'))),

]
