"""
Email Tasks (Async)
"""
from celery import Task
from backend.celery_app import celery_app
from backend.utils.email_service import EmailService
from typing import List


class EmailTask(Task):
    """Email task base"""
    _email_service = None
    
    @property
    def email_service(self):
        if self._email_service is None:
            self._email_service = EmailService()
        return self._email_service


@celery_app.task(base=EmailTask, bind=True, name="backend.tasks.email_tasks.send_email")
def send_email(self, to_email: str, subject: str, body: str, html_body: str = None) -> dict:
    """
    Email gönder (async)
    
    Args:
        to_email: Alıcı email
        subject: Konu
        body: Metin içerik
        html_body: HTML içerik (opsiyonel)
    
    Returns:
        dict: {"status": "success", "message_id": "..."}
    """
    try:
        self.update_state(state="PROGRESS", meta={"status": "Email gönderiliyor..."})
        
        # Email gönder
        result = self.email_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        return {
            "status": "success",
            "to_email": to_email,
            "subject": subject
        }
        
    except Exception as e:
        print(f"Email send error: {e}")
        raise


@celery_app.task(name="backend.tasks.email_tasks.send_bulk_emails")
def send_bulk_emails(emails: List[dict]) -> dict:
    """
    Toplu email gönderimi
    
    Args:
        emails: [{"to": "...", "subject": "...", "body": "..."}, ...]
    
    Returns:
        dict: {"total": 10, "success": 9, "failed": 1}
    """
    success_count = 0
    failed_count = 0
    
    for email_data in emails:
        try:
            send_email(
                email_data["to"],
                email_data["subject"],
                email_data["body"],
                email_data.get("html_body")
            )
            success_count += 1
        except Exception as e:
            print(f"Bulk email error: {e}")
            failed_count += 1
    
    return {
        "total": len(emails),
        "success": success_count,
        "failed": failed_count
    }


@celery_app.task(name="backend.tasks.email_tasks.send_mutabakat_notification")
def send_mutabakat_notification(mutabakat_id: int, notification_type: str) -> dict:
    """
    Mutabakat bildirimi gönder
    
    Args:
        mutabakat_id: Mutabakat ID
        notification_type: "approved", "rejected", "sent"
    
    Returns:
        dict: {"status": "success"}
    """
    from backend.database import get_db
    from backend.models import Mutabakat
    
    db = next(get_db())
    
    try:
        mutabakat = db.query(Mutabakat).filter(Mutabakat.id == mutabakat_id).first()
        if not mutabakat:
            raise ValueError(f"Mutabakat bulunamadı: {mutabakat_id}")
        
        # Notification email'i hazırla
        sender_company = mutabakat.sender.company if mutabakat.sender else None
        notification_email = sender_company.notification_email if sender_company else None
        
        if not notification_email:
            return {"status": "skipped", "reason": "No notification email"}
        
        # Email içeriğini hazırla
        if notification_type == "approved":
            subject = f"Mutabakat Onaylandı - {mutabakat.mutabakat_no}"
            body = f"Mutabakat {mutabakat.mutabakat_no} onaylandı."
        elif notification_type == "rejected":
            subject = f"Mutabakat Reddedildi - {mutabakat.mutabakat_no}"
            body = f"Mutabakat {mutabakat.mutabakat_no} reddedildi. Neden: {mutabakat.red_nedeni}"
        elif notification_type == "sent":
            subject = f"Mutabakat Gönderildi - {mutabakat.mutabakat_no}"
            body = f"Mutabakat {mutabakat.mutabakat_no} başarıyla gönderildi."
        else:
            raise ValueError(f"Geçersiz notification type: {notification_type}")
        
        # Email gönder
        send_email(notification_email, subject, body)
        
        return {"status": "success", "notification_type": notification_type}
        
    finally:
        db.close()

