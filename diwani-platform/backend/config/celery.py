"""
===================================
منصة ديواني - Celery Configuration
Background Tasks & Scheduled Jobs
===================================
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create Celery app
app = Celery('diwani')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all apps
app.autodiscover_tasks()

# ===================================
# Celery Beat Schedule (Periodic Tasks)
# ===================================
app.conf.beat_schedule = {
    # Clean expired OTP codes every hour
    'cleanup-expired-otps': {
        'task': 'apps.notifications.tasks.cleanup_expired_otps',
        'schedule': crontab(minute=0),  # Every hour
    },

    # Clean old notifications daily
    'cleanup-old-notifications': {
        'task': 'apps.notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=4, minute=0),  # 4 AM
    },

    # TODO: Add these tasks when implementing respective apps
    # 'update-store-ratings': {
    #     'task': 'apps.stores.tasks.update_store_ratings',
    #     'schedule': crontab(hour=3, minute=0),  # 3 AM
    # },
    # 'send-order-reminders': {
    #     'task': 'apps.orders.tasks.send_pending_order_reminders',
    #     'schedule': crontab(minute='*/15'),  # Every 15 minutes
    # },
    # 'generate-daily-report': {
    #     'task': 'apps.core.tasks.generate_daily_report',
    #     'schedule': crontab(hour=6, minute=0),  # 6 AM
    # },
    # 'check-driver-activity': {
    #     'task': 'apps.delivery.tasks.check_driver_activity',
    #     'schedule': crontab(minute='*/5'),  # Every 5 minutes
    # },
}

# ===================================
# Task Routing
# ===================================
app.conf.task_routes = {
    'apps.notifications.tasks.*': {'queue': 'notifications'},
    'apps.orders.tasks.*': {'queue': 'orders'},
    'apps.delivery.tasks.*': {'queue': 'delivery'},
    'apps.*.tasks.*': {'queue': 'default'},
}

# ===================================
# Task Configuration
# ===================================
app.conf.task_annotations = {
    '*': {
        'rate_limit': '100/m',  # 100 tasks per minute max
    },
    'apps.notifications.tasks.send_push_notification': {
        'rate_limit': '1000/m',  # Higher rate for notifications
    },
}


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')
    return 'Celery is working!'
