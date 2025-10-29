from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from backend.models import UserRole, MutabakatDurumu

# User Schemas
class UserBase(BaseModel):
    email: Optional[str] = None  # EmailStr yerine str - @temp.mutabakat.local için
    username: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    tax_number: Optional[str] = None
    tax_office: Optional[str] = None  # Vergi Dairesi
    phone: Optional[str] = None
    address: Optional[str] = None
    role: UserRole = UserRole.MUSTERI

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None  # EmailStr yerine str
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    vkn_tckn: Optional[str] = None  # Düzeltildi: tax_number -> vkn_tckn
    tax_office: Optional[str] = None  # Vergi Dairesi
    phone: Optional[str] = None
    address: Optional[str] = None
    ilk_giris_tamamlandi: Optional[bool] = None  # İlk giriş tamamlanma durumu

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    vkn_tckn: Optional[str] = None  # VKN/TC Kimlik No
    ilk_giris_tamamlandi: Optional[bool] = False  # İlk giriş tamamlandı mı?
    company_logo: Optional[str] = None  # Şirket logosu
    created_at: datetime
    
    class Config:
        from_attributes = True
        
    def dict(self, **kwargs):
        """Role enum'unu string'e çevir"""
        data = super().dict(**kwargs)
        if 'role' in data and hasattr(data['role'], 'value'):
            data['role'] = data['role'].value
        return data

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    ilk_giris_tamamlandi: Optional[bool] = True  # İlk giriş kontrolü için
    vkn_tckn: Optional[str] = None  # VKN bilgisi

class TokenData(BaseModel):
    username: Optional[str] = None

# Mutabakat Item Schemas
class MutabakatItemBase(BaseModel):
    tarih: datetime
    belge_no: Optional[str] = None
    aciklama: Optional[str] = None
    borc: float = 0.0
    alacak: float = 0.0

class MutabakatItemCreate(MutabakatItemBase):
    pass

class MutabakatItemResponse(MutabakatItemBase):
    id: int
    mutabakat_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Mutabakat Schemas
class MutabakatBase(BaseModel):
    receiver_id: int
    donem_baslangic: datetime
    donem_bitis: datetime
    toplam_borc: float = 0.0
    toplam_alacak: float = 0.0
    aciklama: Optional[str] = None

class MutabakatCreate(MutabakatBase):
    # Kalemler artık zorunlu değil - sadece bakiye mutabakatı
    pass

class MutabakatUpdate(BaseModel):
    donem_baslangic: Optional[datetime] = None
    donem_bitis: Optional[datetime] = None
    aciklama: Optional[str] = None
    durum: Optional[MutabakatDurumu] = None
    red_nedeni: Optional[str] = None

class UserBasicInfo(BaseModel):
    """Kullanıcı temel bilgileri"""
    id: int
    username: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class MutabakatResponse(MutabakatBase):
    id: int
    mutabakat_no: str
    sender_id: int
    sender: Optional[UserBasicInfo] = None  # Oluşturan kullanıcı bilgisi
    receiver: Optional[UserBasicInfo] = None  # Alıcı kullanıcı bilgisi
    toplam_borc: float
    toplam_alacak: float
    bakiye: float
    durum: MutabakatDurumu
    red_nedeni: Optional[str] = None
    ekstre_talep_edildi: bool = False
    pdf_file_path: Optional[str] = None  # PDF dosya yolu
    gonderim_tarihi: Optional[datetime]
    onay_tarihi: Optional[datetime]
    red_tarihi: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    items: List[MutabakatItemResponse] = []
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class BayiDetayResponse(BaseModel):
    bayi_kodu: str
    bayi_adi: str
    bakiye: float
    
    class Config:
        from_attributes = True

class MutabakatDetailResponse(MutabakatResponse):
    sender: UserResponse
    receiver: UserResponse
    bayi_detaylari: List['BayiDetayResponse'] = []

# Activity Log Schemas
class ActivityLogCreate(BaseModel):
    action: str
    description: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class ActivityLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    description: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Dashboard Stats
class DashboardStats(BaseModel):
    toplam_mutabakat: int
    bekleyen_mutabakat: int
    onaylanan_mutabakat: int
    reddedilen_mutabakat: int
    toplam_borc: float
    toplam_alacak: float

# KVKK Schemas
class KVKKConsentBase(BaseModel):
    kvkk_policy_accepted: bool = False
    customer_notice_accepted: bool = False
    data_retention_accepted: bool = False
    system_consent_accepted: bool = False

class KVKKConsentCreate(KVKKConsentBase):
    """KVKK Onay Kaydetme"""
    pass

class KVKKConsentResponse(BaseModel):
    """KVKK Onay Durumu"""
    id: int
    user_id: int
    kvkk_policy_accepted: bool
    customer_notice_accepted: bool
    data_retention_accepted: bool
    system_consent_accepted: bool
    kvkk_policy_date: Optional[datetime]
    customer_notice_date: Optional[datetime]
    data_retention_date: Optional[datetime]
    system_consent_date: Optional[datetime]
    ip_address: Optional[str]
    isp: Optional[str]
    city: Optional[str]
    country: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class KVKKTextsResponse(BaseModel):
    """KVKK Metinleri"""
    kvkk_policy: dict
    customer_notice: dict
    data_retention: dict
    system_consent: dict

