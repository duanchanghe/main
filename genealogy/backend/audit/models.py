import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AuditLog(models.Model):
    """审计日志 - 记录所有关键操作"""
    
    class Action(models.TextChoices):
        CREATE = 'create', '创建'
        UPDATE = 'update', '更新'
        DELETE = 'delete', '删除'
        LOGIN = 'login', '登录'
        LOGOUT = 'logout', '登出'
        INVITE = 'invite', '邀请'
        JOIN = 'join', '加入'
        UPGRADE = 'upgrade', '升级'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    tenant = models.ForeignKey('tenant.Tenant', on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    
    action = models.CharField(max_length=20, choices=Action.choices)
    resource_type = models.CharField(max_length=50, verbose_name='资源类型')
    resource_id = models.CharField(max_length=100, blank=True, verbose_name='资源ID')
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_id = models.CharField(max_length=50, blank=True, verbose_name='请求ID')
    
    old_value = models.JSONField(null=True, blank=True, verbose_name='旧值')
    new_value = models.JSONField(null=True, blank=True, verbose_name='新值')
    
    status = models.CharField(max_length=20, default='success', verbose_name='状态')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = '审计日志'
        verbose_name_plural = '审计日志'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['action', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user} {self.get_action_display()} {self.resource_type} at {self.timestamp}"


class ActivityLog(models.Model):
    """活动日志 - 用于动态/时间线展示"""
    
    class ActivityType(models.TextChoices):
        MEMBER_ADDED = 'member_added', '添加成员'
        MEMBER_UPDATED = 'member_updated', '更新成员'
        MEMBER_DELETED = 'member_deleted', '删除成员'
        MEMBER_PHOTO = 'member_photo', '上传照片'
        INVITATION_SENT = 'invitation_sent', '发送邀请'
        USER_JOINED = 'user_joined', '用户加入'
        PLAN_CHANGED = 'plan_changed', '计划变更'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenant.Tenant', on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activities')
    
    activity_type = models.CharField(max_length=30, choices=ActivityType.choices)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    member = models.ForeignKey('family.Member', on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'activity_logs'
        verbose_name = '活动日志'
        verbose_name_plural = '活动日志'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.title} - {self.timestamp}"
