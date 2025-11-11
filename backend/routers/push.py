"""
Push Notification Router
Web Push Notification subscription yönetimi
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from backend.database import get_db
from backend.models import User, PushSubscription
from backend.auth import get_current_active_user
from backend.utils.push_service import push_service
from backend.logger import logger
from datetime import datetime

router = APIRouter(prefix="/api/push", tags=["Push Notifications"])


class PushSubscriptionRequest(BaseModel):
    """Push subscription kayıt talebi"""
    endpoint: str
    keys: Dict[str, str]  # {"p256dh": "...", "auth": "..."}
    user_agent: Optional[str] = None
    device_info: Optional[str] = None


class PushSubscriptionResponse(BaseModel):
    """Push subscription response"""
    id: int
    user_id: int
    enabled: bool
    created_at: str
    updated_at: str


@router.post("/subscribe", response_model=PushSubscriptionResponse)
def subscribe_push(
    subscription_data: PushSubscriptionRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Push notification subscription kaydet
    
    Args:
        subscription_data: Push subscription bilgileri
        request: Request objesi
        current_user: Mevcut kullanıcı
        db: Database session
        
    Returns:
        PushSubscriptionResponse: Kaydedilen subscription
    """
    try:
        # Mevcut subscription var mı kontrol et (aynı endpoint için)
        existing = db.query(PushSubscription).filter(
            PushSubscription.user_id == current_user.id,
            PushSubscription.endpoint == subscription_data.endpoint
        ).first()
        
        if existing:
            # Güncelle
            existing.p256dh = subscription_data.keys.get('p256dh', '')
            existing.auth = subscription_data.keys.get('auth', '')
            existing.user_agent = subscription_data.user_agent or request.headers.get('User-Agent', '')
            existing.device_info = subscription_data.device_info
            existing.enabled = True
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            
            logger.info(f"[PUSH] Subscription güncellendi: User {current_user.id}")
            return PushSubscriptionResponse(
                id=existing.id,
                user_id=existing.user_id,
                enabled=existing.enabled,
                created_at=existing.created_at.isoformat(),
                updated_at=existing.updated_at.isoformat()
            )
        else:
            # Yeni subscription oluştur
            subscription = PushSubscription(
                user_id=current_user.id,
                company_id=current_user.company_id,
                endpoint=subscription_data.endpoint,
                p256dh=subscription_data.keys.get('p256dh', ''),
                auth=subscription_data.keys.get('auth', ''),
                user_agent=subscription_data.user_agent or request.headers.get('User-Agent', ''),
                device_info=subscription_data.device_info,
                enabled=True
            )
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            logger.info(f"[PUSH] Yeni subscription kaydedildi: User {current_user.id}")
            return PushSubscriptionResponse(
                id=subscription.id,
                user_id=subscription.user_id,
                enabled=subscription.enabled,
                created_at=subscription.created_at.isoformat(),
                updated_at=subscription.updated_at.isoformat()
            )
            
    except Exception as e:
        logger.error(f"[PUSH] Subscription kaydetme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subscription kaydedilemedi: {str(e)}"
        )


@router.delete("/unsubscribe")
def unsubscribe_push(
    subscription_id: Optional[int] = None,
    endpoint: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Push notification subscription iptal et
    
    Args:
        subscription_id: Subscription ID (opsiyonel)
        endpoint: Subscription endpoint (opsiyonel)
        current_user: Mevcut kullanıcı
        db: Database session
    """
    try:
        if subscription_id:
            subscription = db.query(PushSubscription).filter(
                PushSubscription.id == subscription_id,
                PushSubscription.user_id == current_user.id
            ).first()
        elif endpoint:
            subscription = db.query(PushSubscription).filter(
                PushSubscription.endpoint == endpoint,
                PushSubscription.user_id == current_user.id
            ).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="subscription_id veya endpoint belirtilmelidir"
            )
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription bulunamadı"
            )
        
        # Subscription'ı sil
        db.delete(subscription)
        db.commit()
        
        logger.info(f"[PUSH] Subscription silindi: User {current_user.id}, ID {subscription.id}")
        return {"success": True, "message": "Subscription iptal edildi"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PUSH] Subscription silme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subscription silinemedi: {str(e)}"
        )


@router.get("/status")
def get_push_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcının push notification durumunu getir
    
    Args:
        current_user: Mevcut kullanıcı
        db: Database session
        
    Returns:
        dict: Push notification durumu
    """
    subscriptions = db.query(PushSubscription).filter(
        PushSubscription.user_id == current_user.id,
        PushSubscription.enabled == True
    ).all()
    
    return {
        "enabled": len(subscriptions) > 0,
        "subscription_count": len(subscriptions),
        "subscriptions": [
            {
                "id": sub.id,
                "endpoint": sub.endpoint[:50] + "..." if len(sub.endpoint) > 50 else sub.endpoint,
                "device_info": sub.device_info,
                "created_at": sub.created_at.isoformat(),
                "last_notification_sent": sub.last_notification_sent.isoformat() if sub.last_notification_sent else None
            }
            for sub in subscriptions
        ],
        "vapid_public_key": os.getenv('VAPID_PUBLIC_KEY') if push_service.enabled else None
    }


@router.post("/test")
def test_push_notification(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Test push notification gönder (sadece kendi subscription'larına)
    
    Args:
        current_user: Mevcut kullanıcı
        db: Database session
    """
    subscriptions = db.query(PushSubscription).filter(
        PushSubscription.user_id == current_user.id,
        PushSubscription.enabled == True
    ).all()
    
    if not subscriptions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aktif push subscription bulunamadı"
        )
    
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
    
    # Test bildirimi gönder
    result = push_service.send_to_user(
        subscriptions=sub_list,
        title="🧪 Test Bildirimi",
        body="Bu bir test bildirimidir. Push notifications çalışıyor!",
        data={"type": "test", "timestamp": datetime.utcnow().isoformat()},
        tag="test-notification"
    )
    
    # Son gönderim zamanını güncelle
    for sub in subscriptions:
        sub.last_notification_sent = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Test bildirimi gönderildi",
        "result": result
    }

