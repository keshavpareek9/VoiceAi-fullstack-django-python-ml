from django.contrib import admin
from django.urls import path, include
from voice_command import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('api/', include('voice_command.urls')),
]
