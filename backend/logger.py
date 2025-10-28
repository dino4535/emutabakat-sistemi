import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from sqlalchemy.orm import Session
from backend.models import ActivityLog
from typing import Optional

# Log klasörünü oluştur
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Logging ayarları
log_file = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d')}.log")

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# File Handler (Rotating)
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=10,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Root Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def log_activity(
    db: Session,
    action: str,
    description: Optional[str] = None,
    user_id: Optional[int] = None,
    ip_info: Optional[dict] = None,  # ISP bilgili IP (dict veya string)
    ip_address: Optional[str] = None,  # Geriye dönük uyumluluk
    user_agent: Optional[str] = None,
    company_id: Optional[int] = None  # Multi-company için
):
    """Aktivite logunu veritabanına kaydet - ISP bilgili (Yasal Delil için) - Multi-Company"""
    try:
        # ISP bilgisini parse et
        if ip_info:
            if isinstance(ip_info, dict):
                ip_addr = ip_info.get('ip', 'unknown')
                isp = ip_info.get('isp')
                city = ip_info.get('city')
                country = ip_info.get('country')
                org = ip_info.get('org')
            else:
                # String ise sadece IP
                ip_addr = str(ip_info)
                isp = city = country = org = None
        else:
            # Geriye dönük uyumluluk
            ip_addr = ip_address
            isp = city = country = org = None
        
        log_entry = ActivityLog(
            company_id=company_id,  # Multi-company için
            user_id=user_id,
            action=action,
            description=description,
            ip_address=ip_addr,
            user_agent=user_agent,
            isp=isp,
            city=city,
            country=country,
            organization=org
        )
        db.add(log_entry)
        db.commit()
        
        # Console'a yaz (ISP bilgili)
        if isp:
            logger.info(f"[{action}] User: {user_id}, IP: {ip_addr} ({isp} - {city}, {country}), Desc: {description}")
        else:
            logger.info(f"[{action}] User: {user_id}, IP: {ip_addr}, Desc: {description}")
        
    except Exception as e:
        logger.error(f"Log kaydetme hatası: {e}")
        db.rollback()

class ActivityLogger:
    """Aktivite loglama helper class - ISP Bilgili (Yasal Delil için) - Multi-Company"""
    
    @staticmethod
    def log(db: Session, action: str, description: str, user_id: int, ip_info, user_agent: str = None, company_id: int = None):
        """Genel log metodu - ISP bilgili - Multi-Company"""
        log_activity(db, action, description, user_id, ip_info=ip_info, user_agent=user_agent, company_id=company_id)
    
    @staticmethod
    def log_login(db: Session, user_id: int, ip_info, user_agent: str):
        """Login - ISP bilgili"""
        log_activity(db, "LOGIN", "Kullanıcı giriş yaptı", user_id, ip_info=ip_info, user_agent=user_agent)
    
    @staticmethod
    def log_logout(db: Session, user_id: int, ip_info):
        """Logout - ISP bilgili"""
        log_activity(db, "LOGOUT", "Kullanıcı çıkış yaptı", user_id, ip_info=ip_info)
    
    @staticmethod
    def log_mutabakat_created(db: Session, user_id: int, mutabakat_no: str, ip_info):
        """Mutabakat oluşturma - ISP bilgili (Yasal Delil)"""
        log_activity(db, "MUTABAKAT_OLUSTUR", f"Mutabakat oluşturuldu: {mutabakat_no}", user_id, ip_info=ip_info)
    
    @staticmethod
    def log_mutabakat_sent(db: Session, user_id: int, mutabakat_no: str, ip_info):
        """Mutabakat gönderme - ISP bilgili (Yasal Delil)"""
        log_activity(db, "MUTABAKAT_GONDER", f"Mutabakat gönderildi: {mutabakat_no}", user_id, ip_info=ip_info)
    
    @staticmethod
    def log_mutabakat_approved(db: Session, user_id: int, mutabakat_no: str, ip_info):
        """Mutabakat onaylama - ISP bilgili (Yasal Delil)"""
        log_activity(db, "MUTABAKAT_ONAYLA", f"Mutabakat onaylandı: {mutabakat_no}", user_id, ip_info=ip_info)
    
    @staticmethod
    def log_mutabakat_rejected(db: Session, user_id: int, mutabakat_no: str, reason: str, ip_info):
        """Mutabakat reddetme - ISP bilgili (Yasal Delil)"""
        log_activity(db, "MUTABAKAT_REDDET", f"Mutabakat reddedildi: {mutabakat_no}, Neden: {reason}", user_id, ip_info=ip_info)
    
    @staticmethod
    def log_user_created(db: Session, admin_id: int, new_user_email: str, ip: str):
        log_activity(db, "KULLANICI_OLUSTUR", f"Yeni kullanıcı: {new_user_email}", admin_id, ip)
    
    @staticmethod
    def log_user_updated(db: Session, admin_id: int, updated_user_id: int, ip: str):
        log_activity(db, "KULLANICI_GUNCELLE", f"Kullanıcı güncellendi: {updated_user_id}", admin_id, ip)
    
    @staticmethod
    def log_error(db: Session, error_msg: str, user_id: Optional[int] = None, ip: Optional[str] = None):
        log_activity(db, "ERROR", error_msg, user_id, ip)
        logger.error(error_msg)
    
    @staticmethod
    def log_activity(db: Session, user_id: int, action: str, description: str, ip: str):
        """Genel aktivite log metodu"""
        log_activity(db, action, description, user_id, ip)

