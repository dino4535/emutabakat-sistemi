"""
Audit Log Yardımcı Fonksiyonları
Tüm kritik işlemleri otomatik olarak loglamak için decorator ve helper fonksiyonlar
"""

from functools import wraps
from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.orm import Session
import json
import traceback
from datetime import datetime
import time

from backend.models import AuditLog, AuditLogAction, User


def get_client_info(request: Request) -> Dict[str, str]:
    """Request'ten client bilgilerini çıkar"""
    return {
        'ip_address': request.client.host if request.client else 'unknown',
        'user_agent': request.headers.get('user-agent', ''),
        'http_method': request.method,
        'endpoint': str(request.url.path)
    }


def sanitize_request_data(data: Any, sensitive_fields: list = None) -> str:
    """
    Request data'yı JSON string'e çevir ve hassas bilgileri maskele
    """
    if sensitive_fields is None:
        sensitive_fields = ['password', 'hashed_password', 'token', 'api_key', 
                          'secret', 'certificate_password', 'sms_password']
    
    if isinstance(data, dict):
        sanitized = data.copy()
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '***MASKED***'
        return json.dumps(sanitized, ensure_ascii=False, default=str)
    
    return str(data)


def create_audit_log(
    db: Session,
    action: AuditLogAction,
    user: Optional[User] = None,
    action_description: str = None,
    status: str = 'success',
    target_model: str = None,
    target_id: int = None,
    target_identifier: str = None,
    old_values: Dict = None,
    new_values: Dict = None,
    request: Request = None,
    response_status: int = None,
    error_message: str = None,
    error_traceback: str = None,
    duration_ms: int = None,
    ip_info: Dict = None
) -> AuditLog:
    """
    Audit log kaydı oluştur
    
    Args:
        db: Database session
        action: İşlem türü (AuditLogAction enum)
        user: İşlemi yapan kullanıcı
        action_description: İşlem açıklaması
        status: İşlem durumu (success, failed, error)
        target_model: İşlem yapılan model adı
        target_id: İşlem yapılan kaydın ID'si
        target_identifier: İşlem yapılan kaydın tanımlayıcısı
        old_values: Eski değerler (dict)
        new_values: Yeni değerler (dict)
        request: FastAPI Request objesi
        response_status: HTTP response status code
        error_message: Hata mesajı
        error_traceback: Hata detayı
        duration_ms: İşlem süresi (ms)
        ip_info: IP bilgileri (isp, city, country)
    """
    
    # Client bilgileri
    client_info = {}
    if request:
        client_info = get_client_info(request)
    
    # Kullanıcı bilgileri
    user_id = user.id if user else None
    username = user.username if user else 'anonymous'
    user_role = str(user.role) if user else None
    company_id = user.company_id if user else None
    company_name = user.company.company_name if (user and user.company) else None
    
    # IP bilgileri (ip_info'dan)
    isp = ip_info.get('isp', '') if ip_info else ''
    city = ip_info.get('city', '') if ip_info else ''
    country = ip_info.get('country', '') if ip_info else ''
    
    # Audit log kaydı oluştur
    audit_log = AuditLog(
        action=action,
        action_description=action_description,
        status=status,
        user_id=user_id,
        username=username,
        user_role=user_role,
        company_id=company_id,
        company_name=company_name,
        target_model=target_model,
        target_id=target_id,
        target_identifier=target_identifier,
        old_values=json.dumps(old_values, ensure_ascii=False, default=str) if old_values else None,
        new_values=json.dumps(new_values, ensure_ascii=False, default=str) if new_values else None,
        ip_address=client_info.get('ip_address', ip_info.get('ip', 'unknown') if ip_info else 'unknown'),
        user_agent=client_info.get('user_agent', ''),
        isp=isp,
        city=city,
        country=country,
        http_method=client_info.get('http_method', ''),
        endpoint=client_info.get('endpoint', ''),
        request_data=None,  # Request data'yı burada eklemiyoruz (çok büyük olabilir)
        response_status=response_status,
        error_message=error_message,
        error_traceback=error_traceback,
        duration_ms=duration_ms
    )
    
    try:
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log
    except Exception as e:
        db.rollback()
        print(f"[AUDIT LOG ERROR] Audit log kaydedilemedi: {e}")
        # Audit log hatası kritik sistem hatasına yol açmamalı
        return None


def audit_log_decorator(
    action: AuditLogAction,
    target_model: str = None,
    description: str = None
):
    """
    Decorator: Fonksiyonları otomatik olarak audit log'a kaydeder
    
    Kullanım:
        @audit_log_decorator(AuditLogAction.MUTABAKAT_CREATE, target_model='Mutabakat')
        async def create_mutabakat(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            error_msg = None
            error_tb = None
            result = None
            
            # Fonksiyonu çalıştır
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                error_msg = str(e)
                error_tb = traceback.format_exc()
                raise
            finally:
                # İşlem süresini hesapla
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Audit log oluştur (kwargs'tan db, user, request'i al)
                db = kwargs.get('db')
                current_user = kwargs.get('current_user')
                request = kwargs.get('request')
                
                if db:
                    try:
                        create_audit_log(
                            db=db,
                            action=action,
                            user=current_user,
                            action_description=description or f"{action.value} işlemi",
                            status=status,
                            target_model=target_model,
                            request=request,
                            error_message=error_msg,
                            error_traceback=error_tb,
                            duration_ms=duration_ms
                        )
                    except Exception as audit_error:
                        print(f"[AUDIT LOG] Loglama hatası: {audit_error}")
        
        return wrapper
    return decorator


def log_login_attempt(
    db: Session,
    username: str,
    success: bool,
    ip_address: str,
    user_agent: str,
    error_message: str = None,
    user: User = None,
    ip_info: Dict = None
):
    """Login denemesini logla"""
    action = AuditLogAction.LOGIN if success else AuditLogAction.LOGIN_FAILED
    status = 'success' if success else 'failed'
    
    create_audit_log(
        db=db,
        action=action,
        user=user,
        action_description=f"Login {'başarılı' if success else 'başarısız'}: {username}",
        status=status,
        target_model='User',
        target_identifier=username,
        error_message=error_message,
        ip_info=ip_info or {'ip': ip_address, 'user_agent': user_agent}
    )


def log_mutabakat_action(
    db: Session,
    action: AuditLogAction,
    mutabakat,
    user: User,
    description: str = None,
    old_values: Dict = None,
    new_values: Dict = None,
    ip_info: Dict = None,
    request: Request = None
):
    """Mutabakat işlemini logla"""
    create_audit_log(
        db=db,
        action=action,
        user=user,
        action_description=description or f"{action.value}: {mutabakat.mutabakat_no}",
        target_model='Mutabakat',
        target_id=mutabakat.id,
        target_identifier=mutabakat.mutabakat_no,
        old_values=old_values,
        new_values=new_values,
        ip_info=ip_info,
        request=request
    )


def log_user_action(
    db: Session,
    action: AuditLogAction,
    target_user: User,
    current_user: User,
    description: str = None,
    old_values: Dict = None,
    new_values: Dict = None,
    ip_info: Dict = None,
    request: Request = None
):
    """Kullanıcı yönetimi işlemini logla"""
    create_audit_log(
        db=db,
        action=action,
        user=current_user,
        action_description=description or f"{action.value}: {target_user.username}",
        target_model='User',
        target_id=target_user.id,
        target_identifier=target_user.username,
        old_values=old_values,
        new_values=new_values,
        ip_info=ip_info,
        request=request
    )


def log_bayi_action(
    db: Session,
    action: AuditLogAction,
    bayi,
    user: User,
    description: str = None,
    old_values: Dict = None,
    new_values: Dict = None,
    ip_info: Dict = None,
    request: Request = None
):
    """Bayi/Müşteri işlemini logla"""
    create_audit_log(
        db=db,
        action=action,
        user=user,
        action_description=description or f"{action.value}: {bayi.customer_name}",
        target_model='Bayi',
        target_id=bayi.id,
        target_identifier=bayi.vkn,
        old_values=old_values,
        new_values=new_values,
        ip_info=ip_info,
        request=request
    )

