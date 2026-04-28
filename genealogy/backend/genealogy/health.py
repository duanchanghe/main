"""
Health check endpoints for production monitoring
"""
from django.db import connection
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """基础健康检查"""
    return Response({
        'status': 'healthy',
        'service': 'genealogy-api',
        'version': '1.0.0',
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def health_detailed(request):
    """详细健康检查 - 包括数据库和缓存"""
    checks = {
        'database': False,
        'cache': False,
    }
    
    # 数据库检查
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = True
    except Exception as e:
        checks['database_error'] = str(e)
    
    # 缓存检查
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            checks['cache'] = True
    except Exception as e:
        checks['cache_error'] = str(e)
    
    all_healthy = all(checks.get(k) for k in ['database', 'cache'])
    
    return Response({
        'status': 'healthy' if all_healthy else 'degraded',
        'checks': checks,
        'version': '1.0.0',
    }, status=200 if all_healthy else 503)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """就绪检查 - 用于 Kubernetes"""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return Response({'ready': True})
    except Exception:
        return Response({'ready': False}, status=503)
