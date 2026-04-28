"""
Stripe webhook handlers
"""
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import stripe


@csrf_exempt
def stripe_webhook(request):
    """处理 Stripe webhook 事件"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # 处理事件
    if event['type'] == 'customer.subscription.created':
        _handle_subscription_created(event['data']['object'])
    elif event['type'] == 'customer.subscription.updated':
        _handle_subscription_updated(event['data']['object'])
    elif event['type'] == 'customer.subscription.deleted':
        _handle_subscription_deleted(event['data']['object'])
    elif event['type'] == 'invoice.payment_succeeded':
        _handle_invoice_paid(event['data']['object'])
    elif event['type'] == 'invoice.payment_failed':
        _handle_payment_failed(event['data']['object'])

    return HttpResponse(status=200)


def _handle_subscription_created(subscription):
    """处理订阅创建"""
    from tenant.models import Tenant
    
    customer_id = subscription['customer']
    plan = subscription['metadata'].get('plan', 'basic')
    
    try:
        tenant = Tenant.objects.get(stripe_customer_id=customer_id)
        limits = tenant.get_plan_limits()
        
        tenant.plan = plan
        tenant.max_members = limits['members']
        tenant.max_storage_mb = limits['storage']
        tenant.max_users = limits['users']
        tenant.subscription_start = stripe.util.convert_to_datetime(subscription['current_period_start'])
        tenant.subscription_end = stripe.util.convert_to_datetime(subscription['current_period_end'])
        tenant.is_active = True
        tenant.save()
    except Tenant.DoesNotExist:
        pass


def _handle_subscription_updated(subscription):
    """处理订阅更新"""
    _handle_subscription_created(subscription)


def _handle_subscription_deleted(subscription):
    """处理订阅删除"""
    from tenant.models import Tenant
    
    customer_id = subscription['customer']
    
    try:
        tenant = Tenant.objects.get(stripe_customer_id=customer_id)
        tenant.plan = Tenant.Plan.FREE
        tenant.is_active = True  # Free plan 仍然激活
        limits = tenant.get_plan_limits()
        tenant.max_members = limits['members']
        tenant.max_storage_mb = limits['storage']
        tenant.max_users = limits['users']
        tenant.save()
    except Tenant.DoesNotExist:
        pass


def _handle_invoice_paid(invoice):
    """处理付款成功"""
    pass  # 可以添加发送收据邮件等逻辑


def _handle_payment_failed(invoice):
    """处理付款失败"""
    from tenant.models import Tenant
    from django.core.mail import send_mail
    
    customer_id = invoice['customer']
    
    try:
        tenant = Tenant.objects.get(stripe_customer_id=customer_id)
        # 发送邮件通知
        for membership in tenant.users.filter(role=TenantUser.Role.OWNER):
            send_mail(
                subject='付款失败通知',
                message=f'您的 {tenant.name} 订阅付款失败，请及时处理以避免服务中断。',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[membership.user.email],
                fail_silently=True,
            )
    except (Tenant.DoesNotExist, Exception):
        pass
