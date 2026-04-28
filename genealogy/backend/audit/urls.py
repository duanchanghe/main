from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'audit', views.AuditLogViewSet, basename='audit')
router.register(r'activities', views.ActivityLogViewSet, basename='activity')

urlpatterns = [
    path('', include(router.urls)),
]
