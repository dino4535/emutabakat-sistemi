"""
Audit Log API Endpoints
Sistem loglarını görüntüleme ve filtreleme
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from typing import Optional, List
from datetime import datetime, timedelta

from backend.database import get_db
from backend.models import AuditLog, AuditLogAction, User, UserRole
from backend.auth import get_current_user
from pydantic import BaseModel


router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


# Pydantic Modeller
class AuditLogResponse(BaseModel):
    id: int
    action: str
    action_description: Optional[str]
    status: str
    username: Optional[str]
    user_role: Optional[str]
    company_name: Optional[str]
    target_model: Optional[str]
    target_id: Optional[int]
    target_identifier: Optional[str]
    ip_address: Optional[str]
    isp: Optional[str]
    city: Optional[str]
    country: Optional[str]
    http_method: Optional[str]
    endpoint: Optional[str]
    response_status: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    duration_ms: Optional[int]

    class Config:
        from_attributes = True


class AuditLogStatsResponse(BaseModel):
    total_logs: int
    today_logs: int
    failed_actions: int
    unique_users: int
    top_actions: List[dict]
    recent_errors: List[dict]


@router.get("/", response_model=dict)
async def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    action: Optional[str] = None,
    status: Optional[str] = None,
    username: Optional[str] = None,
    target_model: Optional[str] = None,
    ip_address: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Audit logları listele (filtreleme ve sayfalama ile)
    Sadece admin kullanıcılar erişebilir
    """
    
    # Yetki kontrolü: Sadece admin ve company_admin
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
    
    # Base query
    query = db.query(AuditLog)
    
    # Company admin sadece kendi şirketini görebilir
    if current_user.role == UserRole.COMPANY_ADMIN:
        query = query.filter(AuditLog.company_id == current_user.company_id)
    
    # Filtreler
    if action:
        query = query.filter(AuditLog.action == action)
    
    if status:
        query = query.filter(AuditLog.status == status)
    
    if username:
        query = query.filter(AuditLog.username.ilike(f"%{username}%"))
    
    if target_model:
        query = query.filter(AuditLog.target_model == target_model)
    
    if ip_address:
        query = query.filter(AuditLog.ip_address == ip_address)
    
    # Tarih filtreleri
    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.filter(AuditLog.created_at >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.filter(AuditLog.created_at <= to_date)
        except ValueError:
            pass
    
    # Genel arama (action_description, username, target_identifier)
    if search:
        search_filter = or_(
            AuditLog.action_description.ilike(f"%{search}%"),
            AuditLog.username.ilike(f"%{search}%"),
            AuditLog.target_identifier.ilike(f"%{search}%"),
            AuditLog.error_message.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Toplam kayıt sayısı
    total = query.count()
    
    # Sıralama ve sayfalama
    logs = query.order_by(desc(AuditLog.created_at))\
               .offset((page - 1) * page_size)\
               .limit(page_size)\
               .all()
    
    return {
        "logs": [AuditLogResponse.from_orm(log) for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/stats", response_model=AuditLogStatsResponse)
async def get_audit_log_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Audit log istatistikleri
    Sadece admin kullanıcılar erişebilir
    """
    
    # Yetki kontrolü
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
    
    # Base query
    query = db.query(AuditLog)
    
    # Company admin sadece kendi şirketini görebilir
    if current_user.role == UserRole.COMPANY_ADMIN:
        query = query.filter(AuditLog.company_id == current_user.company_id)
    
    # Toplam log sayısı
    total_logs = query.count()
    
    # Bugünkü loglar
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_logs = query.filter(AuditLog.created_at >= today).count()
    
    # Başarısız işlemler
    failed_actions = query.filter(AuditLog.status.in_(['failed', 'error'])).count()
    
    # Benzersiz kullanıcı sayısı
    unique_users = db.query(func.count(func.distinct(AuditLog.username))).scalar()
    
    # En çok yapılan işlemler (top 5)
    top_actions_query = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    )
    
    if current_user.role == UserRole.COMPANY_ADMIN:
        top_actions_query = top_actions_query.filter(AuditLog.company_id == current_user.company_id)
    
    top_actions = top_actions_query.group_by(AuditLog.action)\
                                   .order_by(desc('count'))\
                                   .limit(5)\
                                   .all()
    
    # Son hatalar (top 5)
    recent_errors_query = query.filter(AuditLog.status.in_(['failed', 'error']))\
                              .order_by(desc(AuditLog.created_at))\
                              .limit(5)
    
    recent_errors = [
        {
            'action': log.action.value,
            'error_message': log.error_message,
            'username': log.username,
            'created_at': log.created_at.isoformat()
        }
        for log in recent_errors_query.all()
    ]
    
    return {
        "total_logs": total_logs,
        "today_logs": today_logs,
        "failed_actions": failed_actions,
        "unique_users": unique_users,
        "top_actions": [
            {"action": action.value, "count": count}
            for action, count in top_actions
        ],
        "recent_errors": recent_errors
    }


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log_detail(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tek bir audit log kaydının detayını getir
    """
    
    # Yetki kontrolü
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
    
    # Log kaydını bul
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Log kaydı bulunamadı")
    
    # Company admin sadece kendi şirketinin loglarını görebilir
    if current_user.role == UserRole.COMPANY_ADMIN:
        if log.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Bu log kaydına erişim yetkiniz yok")
    
    return AuditLogResponse.from_orm(log)


@router.get("/actions/list")
async def get_available_actions(
    current_user: User = Depends(get_current_user)
):
    """
    Filtreleme için kullanılabilir action türlerini listele
    """
    
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
    
    return {
        "actions": [
            {"value": action.value, "label": action.value.replace('_', ' ').title()}
            for action in AuditLogAction
        ]
    }


@router.get("/export/csv")
async def export_audit_logs_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """
    Audit logları CSV olarak export et
    """
    
    # Yetki kontrolü
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
    
    import csv
    from io import StringIO
    from fastapi.responses import StreamingResponse
    
    # Query
    query = db.query(AuditLog)
    
    if current_user.role == UserRole.COMPANY_ADMIN:
        query = query.filter(AuditLog.company_id == current_user.company_id)
    
    # Tarih filtreleri
    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.filter(AuditLog.created_at >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.filter(AuditLog.created_at <= to_date)
        except ValueError:
            pass
    
    logs = query.order_by(desc(AuditLog.created_at)).all()
    
    # CSV oluştur
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Tarih', 'İşlem', 'Durum', 'Kullanıcı', 'Şirket', 
        'Hedef', 'IP Adresi', 'ISP', 'Şehir', 'Açıklama'
    ])
    
    # Data
    for log in logs:
        writer.writerow([
            log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            log.action.value,
            log.status,
            log.username or '',
            log.company_name or '',
            f"{log.target_model or ''} #{log.target_id or ''}",
            log.ip_address or '',
            log.isp or '',
            log.city or '',
            log.action_description or ''
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )

