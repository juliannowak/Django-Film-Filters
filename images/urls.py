from django.urls import path

from . import views

urlpatterns = [
    path('images/<str:session_key>/', views.image_dashboard, name='key_uploads'),
    path('images/', views.image_dashboard, name='session_uploads'),
    path('', views.createImageUpload,  name='images_create'),
]
