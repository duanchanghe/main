from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'members', views.MemberViewSet, basename='member')
router.register(r'relations', views.RelationViewSet, basename='relation')

urlpatterns = [
    path('', include(router.urls)),
]
