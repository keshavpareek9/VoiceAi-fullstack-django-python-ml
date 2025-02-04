# voice_command/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('say/', views.say, name='say'),
    path('listen/', views.listen, name='listen'),
    path('choose_domain/', views.choose_domain, name='choose_domain'),
    path('stop_audio/', views.stop_audio, name='stop_audio'),
]
