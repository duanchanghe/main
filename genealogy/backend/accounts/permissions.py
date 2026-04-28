from rest_framework import permissions
from tenant.models import TenantUser


class IsTenantAdmin(permissions.BasePermission):
    """检查用户是否为租户管理员"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        tenant_slug = view.kwargs.get('tenant_slug')
        if not tenant_slug:
            return True
        
        return TenantUser.objects.filter(
            tenant__slug=tenant_slug,
            user=request.user,
            role__in=[TenantUser.Role.OWNER, TenantUser.Role.ADMIN],
            is_active=True
        ).exists()


class IsTenantMember(permissions.BasePermission):
    """检查用户是否为租户成员"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        tenant_slug = view.kwargs.get('tenant_slug')
        if not tenant_slug:
            return True
        
        return TenantUser.objects.filter(
            tenant__slug=tenant_slug,
            user=request.user,
            is_active=True
        ).exists()


class CanManageTenant(permissions.BasePermission):
    """检查用户是否有管理租户的权限"""
    message = '您没有管理此租户的权限'
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        tenant_slug = view.kwargs.get('tenant_slug')
        if not tenant_slug:
            return False
        
        membership = TenantUser.objects.filter(
            tenant__slug=tenant_slug,
            user=request.user,
            is_active=True
        ).first()
        
        if not membership:
            return False
        
        return membership.can_manage


class CheckQuota(permissions.BasePermission):
    """检查租户配额"""
    message = '已达到配额限制，请升级您的订阅计划'
    
    def has_permission(self, request, view):
        if request.method not in ['POST', 'PUT', 'PATCH']:
            return True
        
        if not request.user.is_authenticated:
            return False
        
        tenant_slug = request.data.get('tenant_slug') or view.kwargs.get('tenant_slug')
        if not tenant_slug:
            return True
        
        from tenant.models import Tenant
        from family.models import Member
        
        try:
            tenant = Tenant.objects.get(slug=tenant_slug)
            
            if not tenant.is_subscription_valid:
                return False
            
            # 检查成员配额
            if request.method == 'POST' and view.basename == 'member':
                member_count = Member.objects.filter(
                    user__tenant_memberships__tenant=tenant
                ).distinct().count()
                
                if member_count >= tenant.max_members:
                    return False
            
            return True
        except Tenant.DoesNotExist:
            return True
