from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.TenantViewSet, basename='tenant')

urlpatterns = [
    path('', include(router.urls)),
]

# 用户管理 URL（在租户下嵌套）
tenant_user_urls = [
    path('', views.TenantUserViewSet.as_view({'get': 'list', 'post': 'create'}), name='tenant-users'),
    path('<int:pk>/', views.TenantUserViewSet.as_view({
        'get': 'retrieve', 'put': 'update', 'delete': 'destroy'
    }), name='tenant-user-detail'),
    path('me/', views.TenantUserViewSet.as_view({'get': 'me'}), name='tenant-user-me'),
]

# 邀请 URL
invitation_urls = [
    path('', views.InvitationViewSet.as_view({'get': 'list', 'post': 'create'}), name='invitations'),
    path('accept/', views.InvitationViewSet.as_view({'post': 'accept'}), name='invitation-accept'),
]
