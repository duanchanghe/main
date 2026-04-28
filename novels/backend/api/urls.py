from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'novels', views.NovelViewSet, basename='novel')

urlpatterns = [
    # 认证
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/', views.current_user, name='current_user'),

    # 任务管理
    path('jobs/', views.my_jobs, name='my_jobs'),
    path('jobs/<int:job_id>/', views.get_job_status, name='get_job_status'),
    path('jobs/<int:job_id>/cancel/', views.cancel_job, name='cancel_job'),
    path('jobs/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    path('jobs/<int:job_id>/audio/', views.get_audio_url, name='get_audio_url'),
    path('jobs/<int:job_id>/stream/', views.stream_audio, name='stream_audio'),

    # 用户资源
    path('my-novels/', views.my_novels, name='my_novels'),

    # 资源
    path('voices/', views.available_voices, name='available_voices'),
    path('sfx/', views.available_sfx, name='available_sfx'),
    path('bgm-presets/', views.available_bgm_presets, name='bgm_presets'),
    path('voices/info/', views.tts_voices_info, name='tts_voices_info'),
    path('audio/quality/', views.audio_quality_check, name='audio_quality'),

    # 上传
    path('upload-url/', views.get_upload_url, name='get_upload_url'),

    # 小说视图集
    path('', include(router.urls)),
]
