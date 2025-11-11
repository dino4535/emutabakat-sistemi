"""
Push Notification Helper Functions
Mutabakat olaylarında push notification gönderme
"""
from sqlalchemy.orm import Session
from backend.models import User, PushSubscription
from backend.utils.push_service import push_service
from backend.logger import logger
from datetime import datetime


def send_mutabakat_approved_push(
    db: Session,
    sender_id: int,
    mutabakat_no: str,
    receiver_name: str,
    amount: float
):
    """
    Mutabakat onaylandığında gönderene push notification gönder
    
    Args:
        db: Database session
        sender_id: Gönderen kullanıcı ID
        mutabakat_no: Mutabakat numarası
        receiver_name: Alıcı adı
        amount: Mutabakat tutarı
    """
    try:
        # Gönderenin push subscription'larını al
        subscriptions = db.query(PushSubscription).filter(
            PushSubscription.user_id == sender_id,
            PushSubscription.enabled == True
        ).all()
        
        if not subscriptions:
            return
        
        # Subscription'ları formatla
        sub_list = [
            {
                "endpoint": sub.endpoint,
                "p256dh": sub.p256dh,
                "auth": sub.auth,
                "enabled": sub.enabled
            }
            for sub in subscriptions
        ]
        
        # Push notification gönder
        formatted_amount = f"{abs(amount):,.2f} TL"
        result = push_service.send_to_user(
            subscriptions=sub_list,
            title="✅ Mutabakat Onaylandı",
            body=f"{receiver_name} mutabakatınızı onayladı - {mutabakat_no} ({formatted_amount})",
            data={
                "type": "mutabakat_approved",
                "mutabakat_no": mutabakat_no,
                "receiver_name": receiver_name,
                "amount": amount
            },
            tag=f"mutabakat-{mutabakat_no}",
            icon="/favicon.ico"
        )
        
        # Son gönderim zamanını güncelle
        for sub in subscriptions:
            sub.last_notification_sent = datetime.utcnow()
        db.commit()
        
        logger.info(f"[PUSH] Mutabakat onay bildirimi gönderildi: User {sender_id}, {result['sent']} başarılı")
        
    except Exception as e:
        logger.error(f"[PUSH] Mutabakat onay bildirimi gönderme hatası: {e}")


def send_mutabakat_rejected_push(
    db: Session,
    sender_id: int,
    mutabakat_no: str,
    receiver_name: str,
    reason: str,
    amount: float
):
    """
    Mutabakat reddedildiğinde gönderene push notification gönder
    
    Args:
        db: Database session
        sender_id: Gönderen kullanıcı ID
        mutabakat_no: Mutabakat numarası
        receiver_name: Alıcı adı
        reason: Red nedeni
        amount: Mutabakat tutarı
    """
    try:
        # Gönderenin push subscription'larını al
        subscriptions = db.query(PushSubscription).filter(
            PushSubscription.user_id == sender_id,
            PushSubscription.enabled == True
        ).all()
        
        if not subscriptions:
            return
        
        # Subscription'ları formatla
        sub_list = [
            {
                "endpoint": sub.endpoint,
                "p256dh": sub.p256dh,
                "auth": sub.auth,
                "enabled": sub.enabled
            }
            for sub in subscriptions
        ]
        
        # Push notification gönder
        formatted_amount = f"{abs(amount):,.2f} TL"
        result = push_service.send_to_user(
            subscriptions=sub_list,
            title="❌ Mutabakat Reddedildi",
            body=f"{receiver_name} mutabakatınızı reddetti - {mutabakat_no} ({formatted_amount})",
            data={
                "type": "mutabakat_rejected",
                "mutabakat_no": mutabakat_no,
                "receiver_name": receiver_name,
                "reason": reason[:100],  # İlk 100 karakter
                "amount": amount
            },
            tag=f"mutabakat-{mutabakat_no}",
            icon="/favicon.ico"
        )
        
        # Son gönderim zamanını güncelle
        for sub in subscriptions:
            sub.last_notification_sent = datetime.utcnow()
        db.commit()
        
        logger.info(f"[PUSH] Mutabakat red bildirimi gönderildi: User {sender_id}, {result['sent']} başarılı")
        
    except Exception as e:
        logger.error(f"[PUSH] Mutabakat red bildirimi gönderme hatası: {e}")


def send_mutabakat_sent_push(
    db: Session,
    receiver_id: int,
    mutabakat_no: str,
    sender_name: str,
    amount: float
):
    """
    Mutabakat gönderildiğinde alıcıya push notification gönder
    
    Args:
        db: Database session
        receiver_id: Alıcı kullanıcı ID
        mutabakat_no: Mutabakat numarası
        sender_name: Gönderen adı
        amount: Mutabakat tutarı
    """
    try:
        # Alıcının push subscription'larını al
        subscriptions = db.query(PushSubscription).filter(
            PushSubscription.user_id == receiver_id,
            PushSubscription.enabled == True
        ).all()
        
        if not subscriptions:
            return
        
        # Subscription'ları formatla
        sub_list = [
            {
                "endpoint": sub.endpoint,
                "p256dh": sub.p256dh,
                "auth": sub.auth,
                "enabled": sub.enabled
            }
            for sub in subscriptions
        ]
        
        # Push notification gönder
        formatted_amount = f"{abs(amount):,.2f} TL"
        result = push_service.send_to_user(
            subscriptions=sub_list,
            title="📨 Yeni Mutabakat",
            body=f"{sender_name} size mutabakat gönderdi - {mutabakat_no} ({formatted_amount})",
            data={
                "type": "mutabakat_sent",
                "mutabakat_no": mutabakat_no,
                "sender_name": sender_name,
                "amount": amount
            },
            tag=f"mutabakat-{mutabakat_no}",
            icon="/favicon.ico",
            require_interaction=False
        )
        
        # Son gönderim zamanını güncelle
        for sub in subscriptions:
            sub.last_notification_sent = datetime.utcnow()
        db.commit()
        
        logger.info(f"[PUSH] Mutabakat gönderim bildirimi gönderildi: User {receiver_id}, {result['sent']} başarılı")
        
    except Exception as e:
        logger.error(f"[PUSH] Mutabakat gönderim bildirimi gönderme hatası: {e}")

