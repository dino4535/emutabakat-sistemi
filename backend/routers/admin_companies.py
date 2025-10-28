"""
Admin Company Management Router
Sadece admin kullanıcılar şirket yönetebilir
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models import User, Company, UserRole
from backend.auth import get_current_active_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/admin/companies", tags=["Admin - Company Management"])


# Schemas
class CompanyCreate(BaseModel):
    vkn: str
    company_name: str
    full_company_name: Optional[str] = None
    tax_office: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo_path: Optional[str] = None
    primary_color: str = "#667eea"
    secondary_color: str = "#764ba2"
    sms_enabled: bool = True
    sms_provider: str = "netgsm"
    sms_header: Optional[str] = None
    sms_username: Optional[str] = None
    sms_password: Optional[str] = None
    sms_api_key: Optional[str] = None
    notification_email: Optional[str] = None  # Mutabakat bildirimleri için
    kvkk_policy_text: Optional[str] = None
    kvkk_policy_version: str = "1.0"
    customer_notice_text: Optional[str] = None
    customer_notice_version: str = "1.0"
    data_retention_policy_text: Optional[str] = None
    data_retention_version: str = "1.0"
    system_consent_text: Optional[str] = None
    system_consent_version: str = "1.0"


class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    full_company_name: Optional[str] = None
    tax_office: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo_path: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    sms_enabled: Optional[bool] = None
    sms_provider: Optional[str] = None
    sms_header: Optional[str] = None
    sms_username: Optional[str] = None
    sms_password: Optional[str] = None
    sms_api_key: Optional[str] = None
    notification_email: Optional[str] = None  # Mutabakat bildirimleri için
    kvkk_policy_text: Optional[str] = None
    kvkk_policy_version: Optional[str] = None
    customer_notice_text: Optional[str] = None
    customer_notice_version: Optional[str] = None
    data_retention_policy_text: Optional[str] = None
    data_retention_version: Optional[str] = None
    system_consent_text: Optional[str] = None
    system_consent_version: Optional[str] = None
    is_active: Optional[bool] = None


class CompanyResponse(BaseModel):
    id: int
    vkn: str
    company_name: str
    full_company_name: Optional[str] = None
    tax_office: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo_path: Optional[str] = None
    primary_color: str
    secondary_color: str
    sms_enabled: bool
    sms_provider: Optional[str] = None
    sms_header: Optional[str] = None
    sms_username: Optional[str] = None
    # sms_password: Asla döndürme!
    notification_email: Optional[str] = None  # Mutabakat bildirimleri için
    kvkk_policy_text: Optional[str] = None
    kvkk_policy_version: Optional[str] = None
    customer_notice_text: Optional[str] = None
    customer_notice_version: Optional[str] = None
    data_retention_policy_text: Optional[str] = None
    data_retention_version: Optional[str] = None
    system_consent_text: Optional[str] = None
    system_consent_version: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # İstatistikler
    user_count: int = 0
    mutabakat_count: int = 0
    
    class Config:
        from_attributes = True


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Sadece admin kullanıcılar erişebilir"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gereklidir"
        )
    return current_user


@router.get("/", response_model=List[CompanyResponse])
def get_all_companies(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Tüm şirketleri listele (Sadece Admin)"""
    from sqlalchemy import func
    from backend.models import Mutabakat
    
    # Şirketleri al (SQL Server için ORDER BY zorunlu!)
    companies = db.query(Company).order_by(Company.id).offset(skip).limit(limit).all()
    
    # Her şirket için istatistik ekle
    result = []
    for company in companies:
        # Kullanıcı sayısı
        user_count = db.query(func.count(User.id)).filter(User.company_id == company.id).scalar()
        # Mutabakat sayısı
        mutabakat_count = db.query(func.count(Mutabakat.id)).filter(Mutabakat.company_id == company.id).scalar()
        
        company_dict = {
            "id": company.id,
            "vkn": company.vkn,
            "company_name": company.company_name,
            "full_company_name": company.full_company_name,
            "tax_office": company.tax_office,
            "address": company.address,
            "phone": company.phone,
            "email": company.email,
            "website": company.website,
            "logo_path": company.logo_path,
            "primary_color": company.primary_color,
            "secondary_color": company.secondary_color,
            "sms_enabled": company.sms_enabled,
            "sms_provider": company.sms_provider,
            "sms_header": company.sms_header,
            "sms_username": company.sms_username,
            "notification_email": company.notification_email,
            "kvkk_policy_text": company.kvkk_policy_text,
            "kvkk_policy_version": company.kvkk_policy_version,
            "customer_notice_text": company.customer_notice_text,
            "customer_notice_version": company.customer_notice_version,
            "data_retention_policy_text": company.data_retention_policy_text,
            "data_retention_version": company.data_retention_version,
            "system_consent_text": company.system_consent_text,
            "system_consent_version": company.system_consent_version,
            "is_active": company.is_active,
            "created_at": company.created_at,
            "updated_at": company.updated_at,
            "user_count": user_count,
            "mutabakat_count": mutabakat_count
        }
        result.append(company_dict)
    
    return result


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Şirket detayını getir (Sadece Admin)"""
    from sqlalchemy import func
    from backend.models import Mutabakat
    
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Şirket bulunamadı"
        )
    
    # İstatistikler
    user_count = db.query(func.count(User.id)).filter(User.company_id == company.id).scalar()
    mutabakat_count = db.query(func.count(Mutabakat.id)).filter(Mutabakat.company_id == company.id).scalar()
    
    company_dict = {
        "id": company.id,
        "vkn": company.vkn,
        "company_name": company.company_name,
        "full_company_name": company.full_company_name,
        "tax_office": company.tax_office,
        "address": company.address,
        "phone": company.phone,
        "email": company.email,
        "website": company.website,
        "logo_path": company.logo_path,
        "primary_color": company.primary_color,
        "secondary_color": company.secondary_color,
        "sms_enabled": company.sms_enabled,
        "sms_provider": company.sms_provider,
        "sms_header": company.sms_header,
        "sms_username": company.sms_username,
        "kvkk_policy_version": company.kvkk_policy_version,
        "customer_notice_version": company.customer_notice_version,
        "data_retention_version": company.data_retention_version,
        "is_active": company.is_active,
        "created_at": company.created_at,
        "updated_at": company.updated_at,
        "user_count": user_count,
        "mutabakat_count": mutabakat_count
    }
    
    return company_dict


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Yeni şirket oluştur (Sadece Admin)"""
    
    # VKN kontrolü
    existing = db.query(Company).filter(Company.vkn == company_data.vkn).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu VKN ile zaten bir şirket kayıtlı"
        )
    
    # Yeni şirket oluştur
    new_company = Company(
        vkn=company_data.vkn,
        company_name=company_data.company_name,
        full_company_name=company_data.full_company_name,
        tax_office=company_data.tax_office,
        address=company_data.address,
        phone=company_data.phone,
        email=company_data.email,
        website=company_data.website,
        logo_path=company_data.logo_path,
        primary_color=company_data.primary_color,
        secondary_color=company_data.secondary_color,
        sms_enabled=company_data.sms_enabled,
        sms_provider=company_data.sms_provider,
        sms_header=company_data.sms_header,
        sms_username=company_data.sms_username,
        sms_password=company_data.sms_password,
        sms_api_key=company_data.sms_api_key,
        kvkk_policy_text=company_data.kvkk_policy_text,
        kvkk_policy_version=company_data.kvkk_policy_version,
        customer_notice_text=company_data.customer_notice_text,
        customer_notice_version=company_data.customer_notice_version,
        data_retention_policy_text=company_data.data_retention_policy_text,
        data_retention_version=company_data.data_retention_version,
        is_active=True
    )
    
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    
    print(f"[ADMIN] Yeni şirket oluşturuldu: {new_company.company_name} (VKN: {new_company.vkn}) by {current_user.username}")
    
    return {
        "id": new_company.id,
        "vkn": new_company.vkn,
        "company_name": new_company.company_name,
        "full_company_name": new_company.full_company_name,
        "tax_office": new_company.tax_office,
        "address": new_company.address,
        "phone": new_company.phone,
        "email": new_company.email,
        "website": new_company.website,
        "logo_path": new_company.logo_path,
        "primary_color": new_company.primary_color,
        "secondary_color": new_company.secondary_color,
        "sms_enabled": new_company.sms_enabled,
        "sms_provider": new_company.sms_provider,
        "sms_header": new_company.sms_header,
        "sms_username": new_company.sms_username,
        "kvkk_policy_version": new_company.kvkk_policy_version,
        "customer_notice_version": new_company.customer_notice_version,
        "data_retention_version": new_company.data_retention_version,
        "is_active": new_company.is_active,
        "created_at": new_company.created_at,
        "updated_at": new_company.updated_at,
        "user_count": 0,
        "mutabakat_count": 0
    }


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Şirket bilgilerini güncelle (Sadece Admin)"""
    
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Şirket bulunamadı"
        )
    
    # Güncelle (sadece gönderilen alanlar)
    update_data = company_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        # Boş şifre gönderilirse ignore et (güvenlik)
        if key == 'sms_password' and (value is None or value == ''):
            continue
        setattr(company, key, value)
    
    db.commit()
    db.refresh(company)
    
    print(f"[ADMIN] Şirket güncellendi: {company.company_name} (ID: {company.id}) by {current_user.username}")
    
    # İstatistikler
    from sqlalchemy import func
    from backend.models import Mutabakat
    user_count = db.query(func.count(User.id)).filter(User.company_id == company.id).scalar()
    mutabakat_count = db.query(func.count(Mutabakat.id)).filter(Mutabakat.company_id == company.id).scalar()
    
    return {
        "id": company.id,
        "vkn": company.vkn,
        "company_name": company.company_name,
        "full_company_name": company.full_company_name,
        "tax_office": company.tax_office,
        "address": company.address,
        "phone": company.phone,
        "email": company.email,
        "website": company.website,
        "logo_path": company.logo_path,
        "primary_color": company.primary_color,
        "secondary_color": company.secondary_color,
        "sms_enabled": company.sms_enabled,
        "sms_provider": company.sms_provider,
        "sms_header": company.sms_header,
        "sms_username": company.sms_username,
        "kvkk_policy_version": company.kvkk_policy_version,
        "customer_notice_version": company.customer_notice_version,
        "data_retention_version": company.data_retention_version,
        "is_active": company.is_active,
        "created_at": company.created_at,
        "updated_at": company.updated_at,
        "user_count": user_count,
        "mutabakat_count": mutabakat_count
    }


@router.delete("/{company_id}")
def delete_company(
    company_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Şirket sil (Sadece Admin - DİKKATLİ!)"""
    
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Şirket bulunamadı"
        )
    
    # Kullanıcı veya mutabakat varsa silme (güvenlik)
    from sqlalchemy import func
    from backend.models import Mutabakat
    user_count = db.query(func.count(User.id)).filter(User.company_id == company.id).scalar()
    mutabakat_count = db.query(func.count(Mutabakat.id)).filter(Mutabakat.company_id == company.id).scalar()
    
    if user_count > 0 or mutabakat_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bu şirkete ait {user_count} kullanıcı ve {mutabakat_count} mutabakat var. Önce bunları silmelisiniz."
        )
    
    company_name = company.company_name
    db.delete(company)
    db.commit()
    
    print(f"[ADMIN] Şirket silindi: {company_name} (ID: {company_id}) by {current_user.username}")
    
    return {"message": f"Şirket '{company_name}' başarıyla silindi"}

