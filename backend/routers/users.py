from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from backend.database import get_db
from backend.models import User, UserRole, Bayi
from backend.schemas import UserResponse
from backend.auth import get_current_active_user
from backend.permissions import Permissions
from backend.logger import ActivityLogger
from backend.utils.pagination import Paginator, PaginatedResponse, PaginationMetadata, SortableColumns
from pydantic import BaseModel, EmailStr
import bcrypt
import random
import string
from pathlib import Path
from openpyxl import load_workbook
import re

router = APIRouter(prefix="/api/auth", tags=["Kullanıcılar"])


def get_company_slug(company_name: str) -> str:
    """Şirket adından slug oluştur (VKN_CompanySlug formatı için)"""
    # Türkçe karakterleri değiştir
    tr_map = {
        'ı': 'i', 'İ': 'i', 'ş': 's', 'Ş': 's',
        'ğ': 'g', 'Ğ': 'g', 'ü': 'u', 'Ü': 'u',
        'ö': 'o', 'Ö': 'o', 'ç': 'c', 'Ç': 'c'
    }
    
    slug = company_name.lower()
    for tr_char, en_char in tr_map.items():
        slug = slug.replace(tr_char, en_char)
    
    # Sadece alfanumerik karakterleri tut
    slug = re.sub(r'[^a-z0-9]', '', slug)
    
    # İlk 15 karakteri al (çok uzun olmasın)
    return slug[:15] if slug else 'company'


# Pydantic Models
class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    company_name: Optional[str] = None
    vkn_tckn: Optional[str] = None  # Düzeltildi: tax_number -> vkn_tckn
    phone: Optional[str] = None
    address: Optional[str] = None
    role: UserRole
    bayi_kodu: Optional[str] = None  # Müşteri için bayi kodu


class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    vkn_tckn: Optional[str] = None  # Düzeltildi: tax_number -> vkn_tckn
    phone: Optional[str] = None
    address: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class ExcelUserUploadResult(BaseModel):
    toplam: int
    basarili: int
    basarisiz: int
    hatalar: List[dict]
    olusturulan_kullanicilar: List[dict]


# Endpoints
@router.get("/users")
def get_users(
    page: int = 1,
    page_size: int = 50,
    order_by: Optional[str] = "created_at",
    order_direction: str = "desc",
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    date_start: Optional[str] = None,  # Advanced filter: Başlangıç tarihi
    date_end: Optional[str] = None,    # Advanced filter: Bitiş tarihi
    company: Optional[str] = None,     # Advanced filter: Şirket adı
    roles: Optional[str] = None,       # Advanced filter: Çoklu rol (virgülle ayrılmış)
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcıları listele (Multi-Company) - Pagination & Sorting ile
    
    Query Parameters:
        - page: Sayfa numarası (default: 1)
        - page_size: Sayfa başına kayıt (default: 50, max: 200)
        - order_by: Sıralama kolonu (default: created_at)
        - order_direction: Sıralama yönü (asc/desc, default: desc)
        - search: Arama (username, full_name, email, vkn_tckn)
        - role: Rol filtresi
        - is_active: Aktiflik filtresi
        - date_start: Kayıt tarihi başlangıç (YYYY-MM-DD)
        - date_end: Kayıt tarihi bitiş (YYYY-MM-DD)
        - company: Şirket adı filtresi
        - roles: Çoklu rol filtresi (virgülle ayrılmış, örn: "musteri,tedarikci")
    """
    
    # Base query
    query = db.query(User)
    
    # Sistem admini (ADMIN) tüm kullanıcıları görebilir
    if current_user.role == UserRole.ADMIN:
        pass  # Filtreleme yok
    
    # Şirket admini (COMPANY_ADMIN) sadece kendi şirketinin kullanıcılarını görebilir
    elif current_user.role == UserRole.COMPANY_ADMIN:
        query = query.filter(User.company_id == current_user.company_id)
    
    # Diğer roller (MUHASEBE, PLANLAMA, MUSTERI, TEDARIKCI) sadece kendi şirketlerinin müşteri ve tedarikçilerini görebilir
    else:
        query = query.filter(
            User.company_id == current_user.company_id,
            User.is_active == True,
            User.id != current_user.id,
            User.role.in_([UserRole.MUSTERI, UserRole.TEDARIKCI])
        )
    
    # Arama filtresi
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_pattern)) |
            (User.full_name.ilike(search_pattern)) |
            (User.email.ilike(search_pattern)) |
            (User.vkn_tckn.ilike(search_pattern)) |
            (User.company_name.ilike(search_pattern))
        )
    
    # Rol filtresi
    if role:
        try:
            role_enum = UserRole(role)
            query = query.filter(User.role == role_enum)
        except ValueError:
            pass  # Geçersiz rol, filtreleme yok
    
    # Aktiflik filtresi
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Tarih aralığı filtresi (created_at)
    if date_start:
        try:
            start_date = datetime.strptime(date_start, "%Y-%m-%d")
            query = query.filter(User.created_at >= start_date)
        except ValueError:
            pass  # Geçersiz tarih formatı, filtreleme yok
    
    if date_end:
        try:
            # End date'i günün sonuna ayarla (23:59:59)
            end_date = datetime.strptime(date_end, "%Y-%m-%d")
            end_date = end_date.replace(hour=23, minute=59, second=59)
            query = query.filter(User.created_at <= end_date)
        except ValueError:
            pass  # Geçersiz tarih formatı, filtreleme yok
    
    # Şirket adı filtresi
    if company:
        company_pattern = f"%{company}%"
        query = query.filter(User.company_name.ilike(company_pattern))
    
    # Çoklu rol filtresi
    if roles:
        try:
            role_list = [role.strip() for role in roles.split(',')]
            role_enums = [UserRole(r) for r in role_list if r]
            if role_enums:
                query = query.filter(User.role.in_(role_enums))
        except ValueError:
            pass  # Geçersiz rol, filtreleme yok
    
    # Güvenli sıralama kolonu
    safe_order_by = SortableColumns.get_safe_column(order_by, SortableColumns.USER)
    
    # Paginate
    result = Paginator.paginate(
        query=query,
        page=page,
        page_size=page_size,
        order_by=safe_order_by,
        order_direction=order_direction,
        model_class=User
    )
    
    # UserResponse'a dönüştür
    serialized_items = []
    for user in result["items"]:
        user_response = UserResponse.from_orm(user)
        # Pydantic v2 uyumlu serialize
        try:
            user_dict = user_response.model_dump()
        except AttributeError:
            user_dict = user_response.dict()
        serialized_items.append(user_dict)
    
    return {
        "items": serialized_items,
        "metadata": result["metadata"]
    }


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    request: Request,
    user_data: UserCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Yeni kullanıcı oluştur - Multi-Company (Admin ve Company Admin)
    """
    # Yetki kontrolü
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kullanıcı oluşturma yetkiniz yok"
        )
    
    # Email kontrolü
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi zaten kullanılıyor"
        )
    
    # Company ID belirleme: Company admin ise kendi şirketini atar, sistem admini istediğini atayabilir
    # (Şu an her ikisi de kendi şirketini kullanıyor, ileride sistem admini için farklı şirket seçimi eklenebilir)
    company_id = current_user.company_id
    
    # Company bilgisini al
    from backend.models import Company
    target_company = db.query(Company).filter(Company.id == company_id).first()
    if not target_company:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Şirket bilgisi bulunamadı"
        )
    
    # Username oluştur: VKN_CompanySlug formatında (VKN varsa)
    if user_data.vkn_tckn:
        company_slug = get_company_slug(target_company.company_name)
        generated_username = f"{user_data.vkn_tckn}_{company_slug}"
    else:
        # VKN yoksa, gelen username'i kullan
        generated_username = user_data.username
    
    # Username kontrolü
    existing_username = db.query(User).filter(User.username == generated_username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bu kullanıcı adı zaten kullanılıyor: {generated_username}"
        )
    
    # VKN/TC duplicate kontrolü (Multi-Company: Aynı şirkette aynı VKN olamaz)
    if user_data.vkn_tckn:
        duplicate_vkn = db.query(User).filter(
            User.vkn_tckn == user_data.vkn_tckn,
            User.company_id == company_id
        ).first()
        
        if duplicate_vkn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bu VKN/TC numarası ({user_data.vkn_tckn}) şirketinizde zaten kayıtlı: {duplicate_vkn.full_name or duplicate_vkn.username}"
            )
    
    # Şifreyi hashle
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Kullanıcı oluştur
    new_user = User(
        username=generated_username,  # VKN_CompanySlug formatında
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        company_name=user_data.company_name,
        vkn_tckn=user_data.vkn_tckn,
        phone=user_data.phone,
        address=user_data.address,
        role=user_data.role,
        company_id=company_id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Müşteri rolündeyse otomatik bayi kaydı oluştur
    if user_data.role == UserRole.MUSTERI and user_data.bayi_kodu:
        new_bayi = Bayi(
            user_id=new_user.id,
            bayi_kodu=user_data.bayi_kodu,
            bayi_adi=user_data.company_name or user_data.full_name,
            vkn_tckn=user_data.vkn_tckn or user_data.username,  # VKN/TCKN'yi kullan
            bakiye=0.0,
            donem=None,
            created_at=datetime.utcnow()
        )
        db.add(new_bayi)
        db.commit()
        
        ActivityLogger.log_activity(
            db,
            current_user.id,
            "BAYI_OLUSTUR",
            f"Otomatik bayi oluşturuldu: {user_data.bayi_kodu} - {new_bayi.bayi_adi}",
            request.client.host if request.client else "unknown"
        )
    
    # Log
    ActivityLogger.log_activity(
        db,
        current_user.id,
        "KULLANICI_OLUSTUR",
        f"Yeni kullanıcı oluşturuldu: {new_user.username}",
        request.client.host if request.client else "unknown"
    )
    
    return new_user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    request: Request,
    user_data: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcı güncelle - Multi-Company (Admin ve Company Admin)
    """
    # Yetki kontrolü
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kullanıcı güncelleme yetkiniz yok"
        )
    
    # Kullanıcıyı bul
    user_query = db.query(User).filter(User.id == user_id)
    
    # Company admin ise sadece kendi şirketinin kullanıcılarını güncelleyebilir
    if current_user.role == UserRole.COMPANY_ADMIN:
        user_query = user_query.filter(User.company_id == current_user.company_id)
    
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı veya erişim yetkiniz yok"
        )
    
    # Admin kendisini devre dışı bırakamaz
    if user.id == current_user.id and user_data.is_active == False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kendi hesabınızı devre dışı bırakamazsınız"
        )
    
    # Güncelleme
    if user_data.email:
        # Email kontrolü
        existing = db.query(User).filter(User.email == user_data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu e-posta adresi zaten kullanılıyor"
            )
        user.email = user_data.email
    
    if user_data.password:
        user.hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    if user_data.full_name:
        user.full_name = user_data.full_name
    
    if user_data.company_name is not None:
        user.company_name = user_data.company_name
    
    if user_data.vkn_tckn is not None:
        user.vkn_tckn = user_data.vkn_tckn
    
    if user_data.phone is not None:
        user.phone = user_data.phone
    
    if user_data.address is not None:
        user.address = user_data.address
    
    if user_data.role:
        user.role = user_data.role
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    # Log
    ActivityLogger.log_activity(
        db,
        current_user.id,
        "KULLANICI_GUNCELLE",
        f"Kullanıcı güncellendi: {user.username}",
        request.client.host if request.client else "unknown"
    )
    
    return user


@router.put("/users/{user_id}/toggle-active", status_code=status.HTTP_200_OK)
def toggle_user_active(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcıyı aktif/pasif yap - Multi-Company (Admin ve Company Admin)
    """
    # Yetki kontrolü
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok"
        )
    
    # Kullanıcıyı bul
    user_query = db.query(User).filter(User.id == user_id)
    
    # Company admin ise sadece kendi şirketinin kullanıcılarını aktif/pasif yapabilir
    if current_user.role == UserRole.COMPANY_ADMIN:
        user_query = user_query.filter(User.company_id == current_user.company_id)
    
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı veya erişim yetkiniz yok"
        )
    
    # Admin kendisini pasif yapamaz
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kendi hesabınızı pasif yapamazsınız"
        )
    
    # Durumu değiştir
    user.is_active = not user.is_active
    user.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Log
    action_desc = "aktif" if user.is_active else "pasif"
    ActivityLogger.log_activity(
        db,
        current_user.id,
        "KULLANICI_GUNCELLE",
        f"Kullanıcı {action_desc} yapıldı: {user.username}",
        request.client.host if request.client else "unknown"
    )
    
    return {"message": f"Kullanıcı {action_desc} yapıldı", "is_active": user.is_active}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcıyı kalıcı olarak sil - Multi-Company (Admin ve Company Admin)
    """
    # Yetki kontrolü
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kullanıcı silme yetkiniz yok"
        )
    
    # Kullanıcıyı bul
    user_query = db.query(User).filter(User.id == user_id)
    
    # Company admin ise sadece kendi şirketinin kullanıcılarını silebilir
    if current_user.role == UserRole.COMPANY_ADMIN:
        user_query = user_query.filter(User.company_id == current_user.company_id)
    
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı veya erişim yetkiniz yok"
        )
    
    # Admin kendisini silemez
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kendi hesabınızı silemezsiniz"
        )
    
    # Kalıcı silme
    username = user.username
    db.delete(user)
    db.commit()
    
    # Log
    ActivityLogger.log_activity(
        db,
        current_user.id,
        "KULLANICI_SIL",
        f"Kullanıcı kalıcı olarak silindi: {username}",
        request.client.host if request.client else "unknown"
    )
    
    return None

