"""
Celery Worker Starter
"""
import os
import sys

# Python path'e backend ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.celery_app import celery_app

if __name__ == "__main__":
    # Celery worker'ı başlat
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--pool=solo",  # Windows için solo pool (threading problemlerini önler)
        "--concurrency=4",
        "-Q", "pdf,sms,excel,email,maintenance",  # Tüm queue'ları dinle
    ])

