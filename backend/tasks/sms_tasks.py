"""
SMS Tasks (Async)
"""
from celery import Task
from backend.celery_app import celery_app
from backend.sms import sms_service
from typing import List


@celery_app.task(bind=True, name="backend.tasks.sms_tasks.send_sms")
def send_sms(self, phone: str, message: str, company_id: int) -> dict:
    """
    SMS gönder (async)
    
    Args:
        phone: Telefon numarası
        message: Mesaj
        company_id: Şirket ID
    
    Returns:
        dict: {"status": "success", "phone": "..."}
    """
    from backend.database import get_db
    from backend.models import Company
    
    db = next(get_db())
    
    try:
        self.update_state(state="PROGRESS", meta={"status": "SMS gönderiliyor..."})
        
        # Company bilgilerini al
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError(f"Şirket bulunamadı: {company_id}")
        
        # SMS gönder
        result = sms_service.send_sms(
            phone=phone,
            message=message,
            sms_header=company.sms_header,
            sms_username=company.sms_username,
            sms_password=company.sms_password
        )
        
        return {
            "status": "success" if result else "failed",
            "phone": phone
        }
        
    except Exception as e:
        print(f"SMS send error: {e}")
        raise
    finally:
        db.close()


@celery_app.task(name="backend.tasks.sms_tasks.send_bulk_sms")
def send_bulk_sms(messages: List[dict], company_id: int) -> dict:
    """
    Toplu SMS gönderimi
    
    Args:
        messages: [{"phone": "...", "message": "..."}, ...]
        company_id: Şirket ID
    
    Returns:
        dict: {"total": 10, "success": 9, "failed": 1}
    """
    success_count = 0
    failed_count = 0
    
    for msg in messages:
        try:
            send_sms(msg["phone"], msg["message"], company_id)
            success_count += 1
        except Exception as e:
            print(f"Bulk SMS error: {e}")
            failed_count += 1
    
    return {
        "total": len(messages),
        "success": success_count,
        "failed": failed_count
    }

