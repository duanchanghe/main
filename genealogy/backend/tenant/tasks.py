"""
Celery tasks for tenant management
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_subscription_expiry():
    """检查并更新过期订阅"""
    from .models import Tenant
    
    expired = Tenant.objects.filter(
        subscription_end__lt=timezone.now(),
        is_active=True
    ).exclude(plan=Tenant.Plan.FREE)
    
    count = 0
    for tenant in expired:
        tenant.is_active = False
        tenant.save()
        count += 1
        logger.info(f"Tenant {tenant.slug} subscription expired")
    
    return f"Deactivated {count} expired subscriptions"


@shared_task
def cleanup_expired_invitations():
    """清理过期邀请"""
    from .models import Invitation
    
    expired = Invitation.objects.filter(
        expires_at__lt=timezone.now(),
        status=Invitation.Status.PENDING
    )
    
    count = expired.update(status=Invitation.Status.EXPIRED)
    logger.info(f"Expired {count} invitations")
    
    return f"Expired {count} invitations"


@shared_task
def generate_usage_reports():
    """生成使用报告"""
    from .models import Tenant
    from .serializers import TenantSerializer
    
    reports = []
    for tenant in Tenant.objects.filter(is_active=True):
        serializer = TenantSerializer(tenant)
        reports.append({
            'tenant': tenant.slug,
            'usage': serializer.data
        })
    
    logger.info(f"Generated reports for {len(reports)} tenants")
    return f"Generated reports for {len(reports)} tenants"


@shared_task
def send_invitation_email(invitation_id):
    """发送邀请邮件"""
    from .models import Invitation
    from django.core.mail import send_mail
    from django.conf import settings
    
    try:
        invitation = Invitation.objects.get(id=invitation_id)
        
        subject = f"邀请您加入 {invitation.tenant.name}"
        message = f"""
        您被邀请加入 {invitation.tenant.name} 的家谱。
        
        请点击以下链接接受邀请：
        {settings.FRONTEND_URL}/invite/{invitation.token}
        
        此邀请将在 7 天后过期。
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=False,
        )
        
        logger.info(f"Sent invitation email to {invitation.email}")
        return f"Email sent to {invitation.email}"
    except Invitation.DoesNotExist:
        return f"Invitation {invitation_id} not found"


@shared_task
def notify_plan_upgrade(tenant_id, old_plan, new_plan):
    """通知计划升级"""
    from .models import Tenant
    from django.core.mail import send_mail
    from django.conf import settings
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        
        for membership in tenant.users.filter(is_active=True, role=TenantUser.Role.OWNER):
            subject = f"{tenant.name} 已升级至 {new_plan}"
            message = f"""
            您的家谱 "{tenant.name}" 已成功升级至 {new_plan}。
            
            新配额：
            - 成员数：{tenant.max_members}
            - 存储空间：{tenant.max_storage_mb}MB
            - 用户数：{tenant.max_users}
            
            感谢您的支持！
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[membership.user.email],
                fail_silently=False,
            )
        
        return f"Upgrade notification sent for tenant {tenant_id}"
    except Tenant.DoesNotExist:
        return f"Tenant {tenant_id} not found"


@shared_task
def cleanup_old_audit_logs():
    """清理旧审计日志（保留90天）"""
    from audit.models import AuditLog
    
    cutoff = timezone.now() - timedelta(days=90)
    deleted, _ = AuditLog.objects.filter(timestamp__lt=cutoff).delete()
    
    logger.info(f"Deleted {deleted} old audit logs")
    return f"Deleted {deleted} old audit logs"
