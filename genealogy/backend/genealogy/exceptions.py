from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class APIException(Exception):
    """自定义API异常"""
    def __init__(self, message, code=None, status_code=status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


def custom_exception_handler(exc, context):
    """自定义异常处理器"""
    
    # 调用REST framework的默认异常处理器
    response = exception_handler(exc, context)
    
    if response is not None:
        # 标准化响应格式
        custom_response_data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
            }
        }
        response.data = custom_response_data
        return response
    
    # 处理自定义异常
    if isinstance(exc, APIException):
        logger.warning(f"APIException: {exc.message}")
        return Response({
            'success': False,
            'error': {
                'code': exc.code or exc.status_code,
                'message': exc.message,
            }
        }, status=exc.status_code)
    
    # 未处理的异常
    logger.exception(f"Unhandled exception: {exc}")
    return Response({
        'success': False,
        'error': {
            'code': 500,
            'message': '服务器内部错误，请稍后重试',
        }
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QuotaExceededException(APIException):
    """配额超限异常"""
    def __init__(self, resource='资源'):
        super().__init__(
            message=f'已达到{resource}配额限制，请升级您的订阅计划',
            code='QUOTA_EXCEEDED',
            status_code=status.HTTP_403_FORBIDDEN
        )


class TenantInactiveException(APIException):
    """租户未激活异常"""
    def __init__(self):
        super().__init__(
            message='您的租户已停用，请联系管理员',
            code='TENANT_INACTIVE',
            status_code=status.HTTP_403_FORBIDDEN
        )


class SubscriptionExpiredException(APIException):
    """订阅过期异常"""
    def __init__(self):
        super().__init__(
            message='您的订阅已过期，请续费',
            code='SUBSCRIPTION_EXPIRED',
            status_code=status.HTTP_403_FORBIDDEN
        )


class PermissionDeniedException(APIException):
    """权限不足异常"""
    def __init__(self, message='您没有权限执行此操作'):
        super().__init__(
            message=message,
            code='PERMISSION_DENIED',
            status_code=status.HTTP_403_FORBIDDEN
        )
