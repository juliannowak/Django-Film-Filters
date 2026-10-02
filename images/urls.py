from django.urls import path
from . import views
from pathlib import Path
from django.http import HttpResponse

urlpatterns = [
    path('', views.display_images, name='images'),
    path('images/<str:session_key>/', views.display_images, name='key_images'),
    path('images/', views.display_images, name='session_uploads'), #rename to session_images or images_by_session
    path('cluts/', views.display_cluts, name='cluts'),
    path('cluts/<str:session_key>/', views.display_cluts, name='key_cluts'),
    path('images/delete/<str:session_key>/<int:pk>/', views.delete_image, name='delete_image'),
    path('cluts/delete/<str:session_key>/<int:pk>/', views.delete_clut, name='delete_clut'),
    path('create/', views.create_clut, name='create_clut'),
    path('donate/', views.donate, name='donate'),
    path('about/', views.about, name='about'),

]
