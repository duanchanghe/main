from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response

# Optional django-filter
try:
    from django_filters.rest_framework import DjangoFilterBackend
    HAS_DJANGO_FILTER = True
except ImportError:
    HAS_DJANGO_FILTER = False
    DjangoFilterBackend = None

from .models import AuditLog, ActivityLog
from .serializers import AuditLogSerializer, ActivityLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """审计日志查询"""
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
    
    _filter_backends = []
    if HAS_DJANGO_FILTER:
        _filter_backends.append(DjangoFilterBackend)
    filter_backends = _filter_backends
    
    filterset_fields = ['action', 'resource_type', 'status']
    
    def get_queryset(self):
        queryset = AuditLog.objects.all()
        tenant_slug = self.request.query_params.get('tenant')
        if tenant_slug:
            queryset = queryset.filter(tenant__slug=tenant_slug)
        return queryset


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """活动日志查询"""
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    _filter_backends = []
    if HAS_DJANGO_FILTER:
        _filter_backends.append(DjangoFilterBackend)
    filter_backends = _filter_backends
    
    filterset_fields = ['activity_type']
    
    def get_queryset(self):
        from tenant.models import TenantUser
        
        user_tenants = TenantUser.objects.filter(
            user=self.request.user,
            is_active=True
        ).values_list('tenant_id', flat=True)
        
        return ActivityLog.objects.filter(tenant_id__in=user_tenants)
    
    @action(detail=False, methods=['get'])
    def timeline(self, request):
        """获取活动时间线"""
        activities = self.get_queryset()[:50]
        return Response(ActivityLogSerializer(activities, many=True).data)
