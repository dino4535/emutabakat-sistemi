# -*- coding: utf-8 -*-
"""
Güvenlik Yönetimi Endpoint'leri - Failed Login Tracking & Security
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from backend.database import get_db
from backend.models import User, UserRole, FailedLoginAttempt
from backend.auth import get_current_active_user
from backend.utils.failed_login_tracker import FailedLoginTracker
from backend.logger import ActivityLogger

router = APIRouter(prefix="/api/security", tags=["Güvenlik Yönetimi"])


# Pydantic Schemas
class LockedAccountResponse(BaseModel):
    id: int
    username: str
    vkn_tckn: str
    full_name: Optional[str]
    company_id: int
    company_name: str
    failed_login_count: int
    last_failed_login: Optional[datetime]
    account_locked_until: Optional[datetime]
    account_locked_reason: Optional[str]
    remaining_seconds: Optional[int]
    
    class Config:
        from_attributes = True


class FailedLoginAttemptResponse(BaseModel):
    id: int
    vkn_tckn: str
    username: Optional[str]
    user_id: Optional[int]
    company_id: Optional[int]
    ip_address: str
    user_agent: Optional[str]
    isp: Optional[str]
    city: Optional[str]
    country: Optional[str]
    organization: Optional[str]
    failure_reason: Optional[str]
    attempted_at: datetime
    
    class Config:
        from_attributes = True


class UnlockAccountRequest(BaseModel):
    user_id: int


@router.get("/locked-accounts", response_model=List[LockedAccountResponse])
def get_locked_accounts(
    request: Request,
    company_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kilitli hesapları listele
    
    - ADMIN: Tüm şirketlerdeki kilitli hesapları görebilir
    - COMPANY_ADMIN: Sadece kendi şirketindeki kilitli hesapları görebilir
    """
    # Yetki kontrolü
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok"
        )
    
    # COMPANY_ADMIN ise sadece kendi şirketi
    if current_user.role == UserRole.COMPANY_ADMIN:
        company_id = current_user.company_id
    
    # Kilitli hesapları getir
    locked_users = FailedLoginTracker.get_locked_accounts(db, company_id)
    
    # Response oluştur
    response = []
    for user in locked_users:
        remaining = FailedLoginTracker.get_lockout_time_remaining(user)
        response.append(LockedAccountResponse(
            id=user.id,
            username=user.username,
            vkn_tckn=user.vkn_tckn,
            full_name=user.full_name,
            company_id=user.company_id,
            company_name=user.company.company_name,
            failed_login_count=user.failed_login_count,
            last_failed_login=user.last_failed_login,
            account_locked_until=user.account_locked_until,
            account_locked_reason=user.account_locked_reason,
            remaining_seconds=remaining
        ))
    
    return response


@router.post("/unlock-account")
def unlock_account(
    request: Request,
    data: UnlockAccountRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcı hesabını manuel olarak unlock et
    
    - ADMIN: Tüm şirketlerdeki hesapları unlock edebilir
    - COMPANY_ADMIN: Sadece kendi şirketindeki hesapları unlock edebilir
    """
    # Yetki kontrolü
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok"
        )
    
    # Kullanıcıyı bul
    user = db.query(User).filter(User.id == data.user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı"
        )
    
    # COMPANY_ADMIN ise sadece kendi şirketinden unlock edebilir
    if current_user.role == UserRole.COMPANY_ADMIN and user.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu kullanıcıyı unlock etme yetkiniz yok"
        )
    
    # Unlock et
    FailedLoginTracker.unlock_account(db, user, admin_user_id=current_user.id)
    
    # Log kaydet
    ip_info = {"ip": request.client.host if request.client else "unknown"}
    ActivityLogger.log(
        db=db,
        action="ACCOUNT_UNLOCK",
        description=f"Admin {current_user.username} kullanıcıyı unlock etti: {user.username}",
        user_id=current_user.id,
        ip_info=ip_info,
        user_agent=request.headers.get("user-agent", ""),
        company_id=current_user.company_id
    )
    
    return {
        "success": True,
        "message": f"Kullanıcı {user.username} başarıyla unlock edildi"
    }


@router.get("/failed-login-attempts", response_model=List[FailedLoginAttemptResponse])
def get_failed_login_attempts(
    request: Request,
    user_id: Optional[int] = None,
    vkn_tckn: Optional[str] = None,
    ip_address: Optional[str] = None,
    limit: int = 100,
    hours: int = 24,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Başarısız login denemelerini listele
    
    - ADMIN: Tüm başarısız login denemelerini görebilir
    - COMPANY_ADMIN: Sadece kendi şirketindeki başarısız login denemelerini görebilir
    - Diğer: Sadece kendi başarısız login denemelerini görebilir
    """
    # Yetki kontrolü
    if current_user.role == UserRole.ADMIN:
        # ADMIN her şeyi görebilir
        pass
    elif current_user.role == UserRole.COMPANY_ADMIN:
        # COMPANY_ADMIN sadece kendi şirketini görebilir
        # user_id parametresi verilmişse o kullanıcıyı kontrol et
        if user_id:
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user or target_user.company_id != current_user.company_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu kullanıcının login geçmişini görme yetkiniz yok"
                )
        # vkn_tckn parametresi verilmişse kendi şirketinden olmalı
        if vkn_tckn:
            target_user = db.query(User).filter(
                User.vkn_tckn == vkn_tckn,
                User.company_id == current_user.company_id
            ).first()
            if not target_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu VKN'nin login geçmişini görme yetkiniz yok"
                )
    else:
        # Diğer roller sadece kendilerini görebilir
        user_id = current_user.id
        vkn_tckn = None
        ip_address = None
    
    # Failed login geçmişini getir
    attempts = FailedLoginTracker.get_failed_login_history(
        db=db,
        user_id=user_id,
        vkn_tckn=vkn_tckn,
        ip_address=ip_address,
        limit=limit,
        hours=hours
    )
    
    return attempts


@router.get("/security-stats")
def get_security_stats(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Güvenlik istatistikleri
    
    - ADMIN: Tüm sistem istatistikleri
    - COMPANY_ADMIN: Kendi şirketi istatistikleri
    """
    # Yetki kontrolü
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok"
        )
    
    # Company filtresi
    company_id = current_user.company_id if current_user.role == UserRole.COMPANY_ADMIN else None
    
    # Kilitli hesap sayısı
    locked_accounts = FailedLoginTracker.get_locked_accounts(db, company_id)
    locked_count = len(locked_accounts)
    
    # Son 24 saatteki başarısız login denemeleri
    failed_attempts_24h = FailedLoginTracker.get_failed_login_history(
        db=db,
        hours=24,
        limit=1000
    )
    
    # Company filtresi uygula (COMPANY_ADMIN için)
    if company_id:
        failed_attempts_24h = [a for a in failed_attempts_24h if a.company_id == company_id]
    
    # IP bazlı saldırı analizi (en çok deneme yapan IP'ler)
    ip_counts = {}
    for attempt in failed_attempts_24h:
        ip = attempt.ip_address
        ip_counts[ip] = ip_counts.get(ip, 0) + 1
    
    top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # VKN bazlı saldırı analizi (en çok hedeflenen VKN'ler)
    vkn_counts = {}
    for attempt in failed_attempts_24h:
        vkn = attempt.vkn_tckn
        vkn_counts[vkn] = vkn_counts.get(vkn, 0) + 1
    
    top_vkns = sorted(vkn_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "locked_accounts_count": locked_count,
        "failed_attempts_24h": len(failed_attempts_24h),
        "top_attacking_ips": [{"ip": ip, "count": count} for ip, count in top_ips],
        "top_targeted_vkns": [{"vkn": vkn, "count": count} for vkn, count in top_vkns],
        "company_id": company_id
    }

