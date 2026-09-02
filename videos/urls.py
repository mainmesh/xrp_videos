from django.urls import path
from . import views

app_name = 'videos'

urlpatterns = [
    path('', views.video_list, name='list'),
    path('<int:pk>/', views.video_detail, name='detail'),
    # Legacy atomic completion endpoint (kept for backward compatibility)
    path('<int:pk>/complete/', views.watch_complete, name='complete'),
    path('heartbeat/', views.heartbeat, name='heartbeat'),
    path('upload/', views.video_upload, name='upload'),
    # New atomic credit flow (recommended)
    path('<int:pk>/watch/start/', views.start_watch, name='watch_start'),
    path('<int:pk>/watch/heartbeat/', views.heartbeat_watch, name='watch_heartbeat'),
    path('<int:pk>/watch/complete/', views.complete_watch, name='watch_complete'),
]
