from django.urls import path
from . import views

urlpatterns = [
    # API endpoints
    path('api/recommendations/<int:user_id>/', views.get_user_recommendations_api, name='api_get_recommendations'),
    path('api/add_preference/', views.add_user_preference, name='api_add_preference'),
    path('api/graph_stats/', views.get_graph_stats_api, name='api_get_graph_stats'),

    # HTML page views
    path('', views.home, name='home'),
    path('stats/', views.graph_stats_view, name='graph_stats_view'),
]
