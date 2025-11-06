from django.urls import path

from . import views

urlpatterns = [
    path('images/<str:session_key>/', views.image_dashboard, name='session_uploads'),
    path('images/', views.image_dashboard, name='session_uploads'),
    path('', views.createImageForm,  name='images_create'),
    path('upload_success', views.uploadSuccess, name='success'),
]
