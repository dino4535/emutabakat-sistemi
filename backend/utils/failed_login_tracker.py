# -*- coding: utf-8 -*-
"""
Failed Login Tracking - Brute Force Koruması
"""
from sqlalchemy.orm import Session
from backend.models import User, FailedLoginAttempt, get_turkey_time
from datetime import datetime, timedelta
from typing import Optional, Dict
import pytz

# Türkiye saat dilimi
TURKEY_TZ = pytz.timezone('Europe/Istanbul')

# Konfigürasyon
FAILED_LOGIN_LIMIT = 5  # 5 başarısız deneme sonrası lock
LOCKOUT_DURATION_MINUTES = 15  # 15 dakika lock süresi
FAILED_LOGIN_RESET_MINUTES = 60  # 1 saat içinde 5 deneme (sonra reset)


class FailedLoginTracker:
    """Failed Login Tracking ve Account Locking Yönetimi"""
    
    @staticmethod
    def is_account_locked(user: User) -> tuple[bool, Optional[datetime]]:
        """
        Kullanıcı hesabı kilitli mi?
        
        Returns:
            (is_locked: bool, locked_until: datetime or None)
        """
        if not user.account_locked_until:
            return False, None
        
        now = get_turkey_time()
        
        # Database'den gelen datetime timezone-naive olabilir, timezone ekle
        locked_until = user.account_locked_until
        if locked_until.tzinfo is None:
            locked_until = TURKEY_TZ.localize(locked_until)
        
        # Lock süresi geçmiş mi?
        if now >= locked_until:
            # Lock süresi geçmiş, unlock yap
            return False, None
        
        # Hala locked
        return True, locked_until
    
    @staticmethod
    def lock_account(db: Session, user: User, reason: str = "Too many failed login attempts"):
        """
        Kullanıcı hesabını kilitle
        """
        now = get_turkey_time()
        user.account_locked_until = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        user.account_locked_reason = reason
        user.failed_login_count = 0  # Counter'ı sıfırla (lock sonrası yeniden başlar)
        
        db.commit()
        
        print(f"[SECURITY] Account locked: {user.username} until {user.account_locked_until} ({reason})")
    
    @staticmethod
    def unlock_account(db: Session, user: User, admin_user_id: Optional[int] = None):
        """
        Kullanıcı hesabını manuel olarak unlock et (Admin işlemi)
        """
        user.account_locked_until = None
        user.account_locked_reason = None
        user.failed_login_count = 0
        user.last_failed_login = None
        
        db.commit()
        
        unlock_by = f"by admin (ID: {admin_user_id})" if admin_user_id else "automatically"
        print(f"[SECURITY] Account unlocked: {user.username} {unlock_by}")
    
    @staticmethod
    def record_failed_login(
        db: Session,
        vkn_tckn: str,
        username: Optional[str],
        user: Optional[User],
        ip_address: str,
        user_agent: str,
        isp_info: Dict,
        failure_reason: str
    ):
        """
        Başarısız login denemesini kaydet
        """
        # FailedLoginAttempt kaydı oluştur
        failed_attempt = FailedLoginAttempt(
            vkn_tckn=vkn_tckn,
            username=username,
            user_id=user.id if user else None,
            company_id=user.company_id if user else None,
            ip_address=ip_address,
            user_agent=user_agent,
            isp=isp_info.get("isp"),
            city=isp_info.get("city"),
            country=isp_info.get("country"),
            organization=isp_info.get("organization"),
            failure_reason=failure_reason,
            attempted_at=get_turkey_time()
        )
        
        db.add(failed_attempt)
        db.commit()
        
        print(f"[SECURITY] Failed login attempt recorded: VKN={vkn_tckn}, IP={ip_address}, Reason={failure_reason}")
        
        # Kullanıcı varsa, failed login counter'ı artır
        if user:
            FailedLoginTracker._increment_failed_login_counter(db, user)
    
    @staticmethod
    def _increment_failed_login_counter(db: Session, user: User):
        """
        Kullanıcının failed login counter'ını artır ve gerekirse lock et
        """
        now = get_turkey_time()
        
        # Son başarısız login 1 saatten eski mi? Reset yap
        if user.last_failed_login:
            # Database'den gelen datetime timezone-naive olabilir, timezone ekle
            last_failed = user.last_failed_login
            if last_failed.tzinfo is None:
                last_failed = TURKEY_TZ.localize(last_failed)
            
            time_since_last_failure = now - last_failed
            if time_since_last_failure > timedelta(minutes=FAILED_LOGIN_RESET_MINUTES):
                user.failed_login_count = 0
                print(f"[SECURITY] Failed login counter reset for {user.username} (1 hour passed)")
        
        # Counter'ı artır
        user.failed_login_count += 1
        user.last_failed_login = now
        
        db.commit()
        
        print(f"[SECURITY] Failed login count for {user.username}: {user.failed_login_count}/{FAILED_LOGIN_LIMIT}")
        
        # Limite ulaşıldı mı? Lock et
        if user.failed_login_count >= FAILED_LOGIN_LIMIT:
            FailedLoginTracker.lock_account(
                db,
                user,
                f"Too many failed login attempts ({FAILED_LOGIN_LIMIT} attempts in {FAILED_LOGIN_RESET_MINUTES} minutes)"
            )
    
    @staticmethod
    def reset_failed_login_counter(db: Session, user: User):
        """
        Başarılı login sonrası counter'ı sıfırla
        """
        user.failed_login_count = 0
        user.last_failed_login = None
        # account_locked_until'i sıfırlama (manuel unlock için)
        
        db.commit()
        
        print(f"[SECURITY] Failed login counter reset for {user.username} (successful login)")
    
    @staticmethod
    def get_failed_login_history(
        db: Session,
        user_id: Optional[int] = None,
        vkn_tckn: Optional[str] = None,
        ip_address: Optional[str] = None,
        limit: int = 100,
        hours: int = 24
    ) -> list[FailedLoginAttempt]:
        """
        Başarısız login geçmişini getir
        
        Args:
            user_id: Kullanıcı ID'si (opsiyonel)
            vkn_tckn: VKN/TC (opsiyonel)
            ip_address: IP adresi (opsiyonel)
            limit: Maksimum kayıt sayısı
            hours: Kaç saat geriye gidilecek
        """
        now = get_turkey_time()
        time_threshold = now - timedelta(hours=hours)
        
        query = db.query(FailedLoginAttempt).filter(
            FailedLoginAttempt.attempted_at >= time_threshold
        )
        
        if user_id:
            query = query.filter(FailedLoginAttempt.user_id == user_id)
        
        if vkn_tckn:
            query = query.filter(FailedLoginAttempt.vkn_tckn == vkn_tckn)
        
        if ip_address:
            query = query.filter(FailedLoginAttempt.ip_address == ip_address)
        
        return query.order_by(FailedLoginAttempt.attempted_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_locked_accounts(db: Session, company_id: Optional[int] = None) -> list[User]:
        """
        Kilitli hesapları getir
        
        Args:
            company_id: Şirket ID'si (opsiyonel, ADMIN için tüm şirketler)
        """
        now = get_turkey_time()
        
        query = db.query(User).filter(
            User.account_locked_until.isnot(None),
            User.account_locked_until > now  # Hala locked olan
        )
        
        if company_id:
            query = query.filter(User.company_id == company_id)
        
        return query.order_by(User.account_locked_until.desc()).all()
    
    @staticmethod
    def get_lockout_time_remaining(user: User) -> Optional[int]:
        """
        Kalan lock süresini saniye cinsinden döndür
        
        Returns:
            Kalan süre (saniye) veya None
        """
        if not user.account_locked_until:
            return None
        
        now = get_turkey_time()
        
        if now >= user.account_locked_until:
            return 0
        
        remaining = user.account_locked_until - now
        return int(remaining.total_seconds())

