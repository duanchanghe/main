"""
Celery configuration for genealogy project
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'genealogy.settings')

app = Celery('genealogy')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# Periodic tasks
app.conf.beat_schedule = {
    'check-subscription-expiry': {
        'task': 'tenant.tasks.check_subscription_expiry',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'cleanup-expired-invitations': {
        'task': 'tenant.tasks.cleanup_expired_invitations',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    'generate-usage-reports': {
        'task': 'tenant.tasks.generate_usage_reports',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
