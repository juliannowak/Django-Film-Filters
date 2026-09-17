from django.urls import path
from . import views
from pathlib import Path
from django.http import HttpResponse

def donate(request):
    # Reads the file directly from your project root
    html_path = Path(__file__).resolve().parent / 'templates/donate.html'
    return HttpResponse(html_path.read_text(encoding='utf-8'))

urlpatterns = [
    path('images/<str:session_key>/', views.image_dashboard, name='key_uploads'),
    path('images/', views.image_dashboard, name='session_uploads'),
    path('', views.image_upload,  name='images_create'),
    path('donate/', donate,  name='donate'),
]
