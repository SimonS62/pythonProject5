from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('recommender.urls')),
    path('', lambda request: redirect('recommender/')),
]
