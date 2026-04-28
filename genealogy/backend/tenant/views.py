from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from .models import Tenant, TenantUser, Invitation
from .serializers import (
    TenantSerializer, TenantCreateSerializer,
    TenantUserSerializer, InvitationSerializer, InvitationCreateSerializer
)
from accounts.permissions import IsTenantAdmin


class TenantViewSet(viewsets.ModelViewSet):
    """租户管理视图集"""
    serializer_class = TenantSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Tenant.objects.all()
        return Tenant.objects.filter(users__user=user, users__is_active=True)
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TenantCreateSerializer
        return TenantSerializer
    
    def create(self, request):
        """创建新租户（注册时自动创建）"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tenant = Tenant.objects.create(**serializer.validated_data)
        
        # 自动将创建者设为所有者
        TenantUser.objects.create(
            tenant=tenant,
            user=request.user,
            role=TenantUser.Role.OWNER
        )
        
        return Response(TenantSerializer(tenant).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def usage(self, request, slug=None):
        """获取租户使用情况"""
        tenant = self.get_object()
        from family.models import Member
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        member_count = Member.objects.filter(
            user__tenant_memberships__tenant=tenant
        ).distinct().count()
        
        user_count = tenant.users.filter(is_active=True).count()
        
        # 计算存储使用
        storage_used = 0
        for member in Member.objects.filter(user__tenant_memberships__tenant=tenant).distinct():
            if member.photo:
                try:
                    storage_used += member.photo.size
                except:
                    pass
        
        return Response({
            'members': {
                'used': member_count,
                'limit': tenant.max_members,
                'percentage': round(member_count / tenant.max_members * 100, 1) if tenant.max_members > 0 else 0
            },
            'storage': {
                'used_mb': round(storage_used / 1024 / 1024, 2),
                'limit_mb': tenant.max_storage_mb,
                'percentage': round(storage_used / 1024 / 1024 / tenant.max_storage_mb * 100, 1) if tenant.max_storage_mb > 0 else 0
            },
            'users': {
                'used': user_count,
                'limit': tenant.max_users,
                'percentage': round(user_count / tenant.max_users * 100, 1) if tenant.max_users > 0 else 0
            }
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsTenantAdmin])
    def upgrade(self, request, slug=None):
        """升级订阅计划"""
        tenant = self.get_object()
        new_plan = request.data.get('plan')
        
        if new_plan not in [choice[0] for choice in Tenant.Plan.choices]:
            return Response({'error': '无效的计划'}, status=status.HTTP_400_BAD_REQUEST)
        
        tenant.plan = new_plan
        limits = tenant.get_plan_limits()
        tenant.max_members = limits['members']
        tenant.max_storage_mb = limits['storage']
        tenant.max_users = limits['users']
        tenant.subscription_start = timezone.now()
        tenant.subscription_end = timezone.now() + timedelta(days=30)
        tenant.save()
        
        return Response(TenantSerializer(tenant).data)


class TenantUserViewSet(viewsets.ModelViewSet):
    """租户用户管理"""
    serializer_class = TenantUserSerializer
    
    def get_queryset(self):
        return TenantUser.objects.filter(
            tenant__slug=self.kwargs['tenant_slug'],
            is_active=True
        )
    
    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsTenantAdmin()]
    
    @action(detail=False, methods=['get'])
    def me(self, request, tenant_slug=None):
        """获取当前用户在租户中的信息"""
        membership = get_object_or_404(
            TenantUser,
            tenant__slug=tenant_slug,
            user=request.user,
            is_active=True
        )
        return Response(TenantUserSerializer(membership).data)


class InvitationViewSet(viewsets.ModelViewSet):
    """邀请管理"""
    serializer_class = InvitationSerializer
    
    def get_queryset(self):
        return Invitation.objects.filter(tenant__slug=self.kwargs['tenant_slug'])
    
    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsTenantAdmin()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InvitationCreateSerializer
        return InvitationSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['tenant'] = get_object_or_404(Tenant, slug=self.kwargs['tenant_slug'])
        return context
    
    @action(detail=False, methods=['post'])
    def accept(self, request, tenant_slug=None):
        """接受邀请"""
        token = request.data.get('token')
        invitation = get_object_or_404(Invitation, token=token, status=Invitation.Status.PENDING)
        
        if invitation.is_expired:
            invitation.status = Invitation.Status.EXPIRED
            invitation.save()
            return Response({'error': '邀请已过期'}, status=status.HTTP_400_BAD_REQUEST)
        
        if invitation.email != request.user.email:
            return Response({'error': '此邀请不是发送给您的'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建租户用户关联
        TenantUser.objects.create(
            tenant=invitation.tenant,
            user=request.user,
            role=invitation.role,
            invited_by=invitation.invited_by
        )
        
        invitation.status = Invitation.Status.ACCEPTED
        invitation.save()
        
        return Response({'message': '已成功加入租户'})


class JoinRequestViewSet(viewsets.ViewSet):
    """申请加入租户"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def request(self, request):
        """申请加入租户"""
        slug = request.data.get('tenant_slug')
        tenant = get_object_or_404(Tenant, slug=slug)
        
        if TenantUser.objects.filter(tenant=tenant, user=request.user).exists():
            return Response({'error': '您已是该租户成员'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 发送邮件通知租户管理员（这里简化处理）
        return Response({
            'message': '申请已提交，请等待租户管理员审核',
            'tenant': TenantSerializer(tenant).data
        })
