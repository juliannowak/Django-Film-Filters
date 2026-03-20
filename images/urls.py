from django.urls import path
from . import views

urlpatterns = [
    path('images/<str:session_key>/', views.image_dashboard, name='key_uploads'),
    path('images/', views.image_dashboard, name='session_uploads'),
    path('', views.image_upload,  name='images_create'),
    #path('donate/', views.donate,  name='donate'),
]
