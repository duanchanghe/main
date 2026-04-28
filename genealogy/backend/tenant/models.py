import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Tenant(models.Model):
    """租户模型 - 代表一个独立的家谱组织/家族"""
    
    class Plan(models.TextChoices):
        FREE = 'free', '免费版'
        BASIC = 'basic', '基础版'
        PRO = 'pro', '专业版'
        ENTERPRISE = 'enterprise', '企业版'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name='租户名称')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='URL标识')
    plan = models.CharField(
        max_length=20, 
        choices=Plan.choices, 
        default=Plan.FREE,
        verbose_name='订阅计划'
    )
    
    # 配额限制
    max_members = models.PositiveIntegerField(default=100, verbose_name='最大成员数')
    max_storage_mb = models.PositiveIntegerField(default=100, verbose_name='最大存储(MB)')
    max_users = models.PositiveIntegerField(default=5, verbose_name='最大用户数')
    
    # 订阅信息
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    subscription_start = models.DateTimeField(null=True, blank=True, verbose_name='订阅开始')
    subscription_end = models.DateTimeField(null=True, blank=True, verbose_name='订阅结束')
    
    # 域名绑定
    domain = models.CharField(max_length=255, blank=True, verbose_name='自定义域名')
    
    # 计费
    stripe_customer_id = models.CharField(max_length=100, blank=True, verbose_name='Stripe客户ID')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'tenants'
        verbose_name = '租户'
        verbose_name_plural = '租户'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
    @property
    def is_subscription_valid(self):
        if not self.subscription_start or not self.subscription_end:
            return self.plan == self.Plan.FREE
        now = timezone.now()
        return self.subscription_start <= now <= self.subscription_end
    
    def get_plan_limits(self):
        limits = {
            self.Plan.FREE: {'members': 100, 'storage': 100, 'users': 5},
            self.Plan.BASIC: {'members': 1000, 'storage': 1000, 'users': 20},
            self.Plan.PRO: {'members': 10000, 'storage': 5000, 'users': 50},
            self.Plan.ENTERPRISE: {'members': -1, 'storage': -1, 'users': -1},
        }
        return limits.get(self.plan, limits[self.Plan.FREE])


class TenantUser(models.Model):
    """租户用户关联 - 支持一个用户加入多个租户"""
    
    class Role(models.TextChoices):
        OWNER = 'owner', '所有者'
        ADMIN = 'admin', '管理员'
        MEMBER = 'member', '成员'
        VIEWER = 'viewer', '查看者'
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_memberships')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    
    is_active = models.BooleanField(default=True)
    invited_by = models.ForeignKey(
        User, null=True, blank=True, 
        on_delete=models.SET_NULL, 
        related_name='invitations_sent'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tenant_users'
        verbose_name = '租户用户'
        verbose_name_plural = '租户用户'
        unique_together = ['tenant', 'user']

    def __str__(self):
        return f"{self.user.username} @ {self.tenant.name}"
    
    @property
    def can_manage(self):
        return self.role in [self.Role.OWNER, self.Role.ADMIN]
    
    @property
    def can_invite(self):
        return self.role in [self.Role.OWNER, self.Role.ADMIN]


class Invitation(models.Model):
    """邀请模型"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', '待处理'
        ACCEPTED = 'accepted', '已接受'
        EXPIRED = 'expired', '已过期'
        CANCELLED = 'cancelled', '已取消'
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField(verbose_name='邀请邮箱')
    role = models.CharField(max_length=20, choices=TenantUser.Role.choices, default=TenantUser.Role.MEMBER)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='invitations')
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'invitations'
        verbose_name = '邀请'
        verbose_name_plural = '邀请'

    def __str__(self):
        return f"邀请 {self.email} 加入 {self.tenant.name}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
