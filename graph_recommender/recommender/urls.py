from django.urls import path
from . import views

urlpatterns = [
    # Главная страница
    path('', views.home, name='home'),

    # API для добавления предпочтений (без параметров)
    path('api/preference/add/', views.add_user_preference, name='api_add_preference'),

    # API для рекомендаций (с параметром user_id) - должен быть ПЕРЕД api/stats/
    path('api/recommendations/<int:user_id>/', views.get_user_recommendations_api, name='api_recommendations'),

    # API для статистики
    path('api/stats/', views.get_graph_stats_api, name='graph_stats_api'),

    # Страница статистики
    path('stats/', views.graph_stats_view, name='graph_stats'),
]
