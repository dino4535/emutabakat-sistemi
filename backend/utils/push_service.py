"""
Web Push Notification Service
VAPID keys ile push notification gönderme
"""
import os
import json
from typing import Optional, List, Dict
from pywebpush import webpush, WebPushException
from py_vapid import Vapid01, Vapid02
from backend.logger import logger
import base64


class PushNotificationService:
    """Web Push Notification Servisi"""
    
    def __init__(self):
        """VAPID keys'i yükle"""
        self.vapid_private_key = os.getenv('VAPID_PRIVATE_KEY')
        self.vapid_public_key = os.getenv('VAPID_PUBLIC_KEY')
        self.vapid_email = os.getenv('VAPID_EMAIL', 'noreply@dinogida.com.tr')
        
        if not self.vapid_private_key or not self.vapid_public_key:
            logger.warning("[PUSH] VAPID keys bulunamadı, push notifications devre dışı")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("[PUSH] Push notification servisi aktif")
    
    def send_notification(
        self,
        subscription: Dict,
        title: str,
        body: str,
        icon: Optional[str] = None,
        badge: Optional[str] = None,
        data: Optional[Dict] = None,
        tag: Optional[str] = None,
        require_interaction: bool = False,
        silent: bool = False
    ) -> bool:
        """
        Push notification gönder
        
        Args:
            subscription: Push subscription dict (endpoint, keys: {p256dh, auth})
            title: Bildirim başlığı
            body: Bildirim içeriği
            icon: Bildirim ikonu URL (opsiyonel)
            badge: Badge ikonu URL (opsiyonel)
            data: Ek veri (opsiyonel)
            tag: Bildirim tag'i (aynı tag'li bildirimler replace edilir)
            require_interaction: Kullanıcı etkileşimi gerektirir mi?
            silent: Sessiz bildirim (ses/vibrasyon yok)
            
        Returns:
            bool: Başarılı ise True
        """
        if not self.enabled:
            logger.warning("[PUSH] Servis devre dışı, bildirim gönderilemedi")
            return False
        
        try:
            # Notification payload
            payload = {
                "title": title,
                "body": body,
                "icon": icon or "/favicon.ico",
                "badge": badge or "/favicon.ico",
                "tag": tag,
                "requireInteraction": require_interaction,
                "silent": silent,
                "data": data or {}
            }
            
            # VAPID claims
            vapid_claims = {
                "sub": f"mailto:{self.vapid_email}"
            }
            
            # Web push gönder
            webpush(
                subscription_info=subscription,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=vapid_claims
            )
            
            logger.info(f"[PUSH] Bildirim gönderildi: {title}")
            return True
            
        except WebPushException as e:
            # Subscription geçersiz veya expired
            if e.response and e.response.status_code == 410:
                logger.warning(f"[PUSH] Subscription geçersiz/expired: {subscription.get('endpoint', 'unknown')}")
            else:
                logger.error(f"[PUSH] Bildirim gönderme hatası: {e}")
            return False
        except Exception as e:
            logger.error(f"[PUSH] Bildirim gönderme hatası: {e}")
            return False
    
    def send_to_user(
        self,
        subscriptions: List[Dict],
        title: str,
        body: str,
        icon: Optional[str] = None,
        badge: Optional[str] = None,
        data: Optional[Dict] = None,
        tag: Optional[str] = None
    ) -> Dict:
        """
        Kullanıcının tüm subscription'larına bildirim gönder
        
        Args:
            subscriptions: Push subscription listesi
            title: Bildirim başlığı
            body: Bildirim içeriği
            icon: Bildirim ikonu URL (opsiyonel)
            badge: Badge ikonu URL (opsiyonel)
            data: Ek veri (opsiyonel)
            tag: Bildirim tag'i
            
        Returns:
            dict: {"sent": count, "failed": count, "invalid": count}
        """
        if not subscriptions:
            return {"sent": 0, "failed": 0, "invalid": 0}
        
        sent = 0
        failed = 0
        invalid = 0
        
        for subscription in subscriptions:
            if not subscription.get('enabled', True):
                continue
            
            # Subscription formatını hazırla
            sub_info = {
                "endpoint": subscription['endpoint'],
                "keys": {
                    "p256dh": subscription['p256dh'],
                    "auth": subscription['auth']
                }
            }
            
            result = self.send_notification(
                subscription=sub_info,
                title=title,
                body=body,
                icon=icon,
                badge=badge,
                data=data,
                tag=tag
            )
            
            if result:
                sent += 1
            else:
                # Subscription geçersiz olabilir, invalid olarak işaretle
                invalid += 1
                failed += 1
        
        return {
            "sent": sent,
            "failed": failed,
            "invalid": invalid
        }


# Singleton instance
push_service = PushNotificationService()

