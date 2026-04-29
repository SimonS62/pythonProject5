from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


urlpatterns = [
    path('admin/', admin.site.urls),
    path('recommender/', include('recommender.urls')),
    path('', lambda request: redirect('recommender/')),
]
