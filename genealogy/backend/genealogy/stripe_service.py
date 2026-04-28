"""
Stripe payment integration for subscription management
"""
import stripe
from django.conf import settings
from django.urls import reverse


class StripeService:
    """Stripe 支付服务"""

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_customer(self, email, name, metadata=None):
        """创建 Stripe 客户"""
        return stripe.Customer.create(
            email=email,
            name=name,
            metadata=metadata or {}
        )

    def get_customer(self, customer_id):
        """获取 Stripe 客户"""
        return stripe.Customer.retrieve(customer_id)

    def create_checkout_session(self, customer_id, price_id, success_url, cancel_url):
        """创建订阅 Checkout Session"""
        return stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
        )

    def create_portal_session(self, customer_id, return_url):
        """创建客户管理 Portal Session"""
        return stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )

    def cancel_subscription(self, subscription_id):
        """取消订阅"""
        return stripe.Subscription.cancel(subscription_id)

    def get_subscription(self, subscription_id):
        """获取订阅详情"""
        return stripe.Subscription.retrieve(subscription_id)

    @staticmethod
    def get_price_id(plan):
        """获取套餐对应的 Stripe Price ID"""
        prices = {
            'basic': settings.STRIPE_PRICE_BASIC,
            'pro': settings.STRIPE_PRICE_PRO,
            'enterprise': settings.STRIPE_PRICE_ENTERPRISE,
        }
        return prices.get(plan)


def get_stripe_service():
    return StripeService()
