"""
Celery Application Configuration
Background job processing için
"""
from celery import Celery
from backend.config import settings
import os

# Celery app oluştur
celery_app = Celery(
    "emutabakat",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
    include=[
        "backend.tasks.pdf_tasks",
        "backend.tasks.sms_tasks",
        "backend.tasks.excel_tasks",
        "backend.tasks.email_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Istanbul",
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster"
    },
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Task routing
    task_routes={
        "backend.tasks.pdf_tasks.*": {"queue": "pdf"},
        "backend.tasks.sms_tasks.*": {"queue": "sms"},
        "backend.tasks.excel_tasks.*": {"queue": "excel"},
        "backend.tasks.email_tasks.*": {"queue": "email"},
    },
    
    # Task priority
    task_default_priority=5,
    
    # Retry settings
    task_autoretry_for=(Exception,),
    task_retry_kwargs={"max_retries": 3},
    task_retry_backoff=True,
    task_retry_backoff_max=600,  # 10 minutes
    task_retry_jitter=True,
)

# Celery Beat schedule (periodic tasks)
celery_app.conf.beat_schedule = {
    # Her gün gece yarısı eski logları temizle
    "cleanup-old-logs": {
        "task": "backend.tasks.maintenance_tasks.cleanup_old_logs",
        "schedule": 86400.0,  # 24 hours
        "options": {"queue": "maintenance"}
    },
    # Her hafta password expiry kontrolü
    "check-password-expiry": {
        "task": "backend.tasks.maintenance_tasks.check_password_expiry",
        "schedule": 604800.0,  # 7 days
        "options": {"queue": "maintenance"}
    },
}

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task"""
    print(f"Request: {self.request!r}")

