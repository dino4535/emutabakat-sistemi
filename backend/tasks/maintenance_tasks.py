"""
Maintenance Tasks (Scheduled)
Celery Beat ile periyodik çalışan görevler
"""
from backend.celery_app import celery_app
from backend.database import get_db
from backend.models import ActivityLog, User
from datetime import datetime, timedelta
import pytz


TURKEY_TZ = pytz.timezone('Europe/Istanbul')


@celery_app.task(name="backend.tasks.maintenance_tasks.cleanup_old_logs")
def cleanup_old_logs(days: int = 90) -> dict:
    """
    Eski logları temizle (90 gün öncesi)
    
    Args:
        days: Kaç gün öncesini temizleyeceği
    
    Returns:
        dict: {"deleted_count": 123}
    """
    db = next(get_db())
    
    try:
        cutoff_date = datetime.now(TURKEY_TZ) - timedelta(days=days)
        
        # Eski logları sil
        deleted_count = db.query(ActivityLog).filter(
            ActivityLog.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        print(f"Cleanup: {deleted_count} eski log silindi")
        
        return {
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        print(f"Cleanup error: {e}")
        raise
    finally:
        db.close()


@celery_app.task(name="backend.tasks.maintenance_tasks.check_password_expiry")
def check_password_expiry() -> dict:
    """
    Şifre süresi dolmak üzere olan kullanıcılara email gönder
    
    Returns:
        dict: {"notified_users": 5}
    """
    db = next(get_db())
    
    try:
        # 7 gün içinde şifresi dolacak kullanıcılar
        # (Bu özellik için password_updated_at kolonu gerekli)
        # Şimdilik sadece örnek
        
        notified_count = 0
        
        # users = db.query(User).filter(
        #     User.password_updated_at < datetime.now() - timedelta(days=83)
        # ).all()
        
        # for user in users:
        #     # Email gönder
        #     notified_count += 1
        
        print(f"Password expiry check: {notified_count} kullanıcıya bildirim gönderildi")
        
        return {
            "notified_users": notified_count
        }
        
    except Exception as e:
        print(f"Password expiry check error: {e}")
        raise
    finally:
        db.close()


@celery_app.task(name="backend.tasks.maintenance_tasks.database_backup")
def database_backup() -> dict:
    """
    Database backup oluştur
    
    Returns:
        dict: {"status": "success", "backup_file": "..."}
    """
    # Database backup mantığı
    # Production'da gerçek backup tool kullanılmalı
    pass

