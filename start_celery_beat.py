"""
Celery Beat Starter (Scheduled Tasks)
"""
import os
import sys

# Python path'e backend ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.celery_app import celery_app

if __name__ == "__main__":
    # Celery beat'i başlat
    celery_app.Beat().run()

