from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import pytz
from backend.database import Base

# Türkiye saat dilimi
TURKEY_TZ = pytz.timezone('Europe/Istanbul')

def get_turkey_time():
    """Türkiye saatini döndür (UTC+3)"""
    return datetime.now(TURKEY_TZ)

class UserRole(str, enum.Enum):
    ADMIN = "admin"  # Sistem admini (tüm şirketleri yönetir)
    COMPANY_ADMIN = "company_admin"  # Şirket admini (sadece kendi şirketini yönetir)
    MUHASEBE = "muhasebe"
    PLANLAMA = "planlama"
    MUSTERI = "musteri"
    TEDARIKCI = "tedarikci"

class Company(Base):
    """Şirket Modeli - Multi-Tenant Sistem"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Şirket Bilgileri
    vkn = Column(String(10), unique=True, index=True, nullable=False)  # Şirket VKN'si
    company_name = Column(String(255), nullable=False)  # Firma adı
    full_company_name = Column(Text)  # Tam unvan (örn: Hüseyin ve İbrahim Kaplan Dino Gıda San. Tic. Ltd. Şti.)
    tax_office = Column(String(255))  # Vergi dairesi
    address = Column(Text)  # Adres
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))
    
    # Branding
    logo_path = Column(String(500))  # Logo dosya yolu (örn: frontend/public/logos/dino-logo.png)
    primary_color = Column(String(7), default='#667eea')  # Ana renk (hex)
    secondary_color = Column(String(7), default='#764ba2')  # İkinci renk (hex)
    
    # SMS Ayarları
    sms_enabled = Column(Boolean, default=True)
    sms_provider = Column(String(50), default='netgsm')  # SMS sağlayıcı
    sms_header = Column(String(50))  # SMS başlığı (örn: DINOGIDA)
    sms_username = Column(String(100))  # SMS API username
    sms_password = Column(String(255))  # SMS API password (encrypted)
    sms_api_key = Column(String(255))  # SMS API key
    
    # Email Bildirimleri
    notification_email = Column(String(255))  # Mutabakat sonuç bildirimleri için email
    
    # KVKK Metinleri (Her şirket kendi metinlerini tanımlar)
    kvkk_policy_text = Column(Text)  # KVKK Politikası
    kvkk_policy_version = Column(String(20), default='1.0')
    customer_notice_text = Column(Text)  # Müşteri Aydınlatma Metni
    customer_notice_version = Column(String(20), default='1.0')
    data_retention_policy_text = Column(Text)  # Veri Saklama ve İmha Politikası
    data_retention_version = Column(String(20), default='1.0')
    system_consent_text = Column(Text)  # E-Mutabakat Sistemi Kullanım Onayı
    system_consent_version = Column(String(20), default='1.0')
    
    # Dijital İmza Ayarları
    certificate_path = Column(String(500))  # Dijital imza sertifikası yolu (örn: certificates/bermer.p12)
    certificate_password = Column(String(255))  # Sertifika şifresi (encrypted)
    
    # Sistem Ayarları
    is_active = Column(Boolean, default=True)  # Şirket aktif mi?
    created_at = Column(DateTime, default=get_turkey_time, nullable=False)
    updated_at = Column(DateTime, default=get_turkey_time, onupdate=get_turkey_time)
    
    # İlişkiler
    users = relationship("User", back_populates="company")
    mutabakats = relationship("Mutabakat", back_populates="company")
    kvkk_consents = relationship("KVKKConsent", back_populates="company")
    activity_logs = relationship("ActivityLog", back_populates="company")

class MutabakatDurumu(str, enum.Enum):
    TASLAK = "taslak"
    GONDERILDI = "gonderildi"
    ONAYLANDI = "onaylandi"
    REDDEDILDI = "reddedildi"
    IPTAL = "iptal"

class User(Base):
    """Kullanıcı Modeli - VKN/TC Kimlik Bazlı (Multi-Company)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-Company: Aynı VKN/TC farklı şirketlerde olabilir
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    vkn_tckn = Column(String(11), index=True, nullable=False)  # Artık unique DEĞİL (company_id ile birlikte unique)
    bayi_kodu = Column(String(50), index=True)  # Her şirketteki bayi kodu (örn: D-12345)
    
    username = Column(String(100), unique=True, index=True, nullable=False)  # Geriye dönük uyumluluk için
    hashed_password = Column(String(255), nullable=False)  # VKN'nin son 6 hanesi (hash'li)
    
    # Profil Bilgileri (İlk giriş sonrası doldurulacak)
    full_name = Column(String(255))
    company_name = Column(String(255))  # Müşteri firma adı (User'ın kendi firması, Company değil)
    tax_number = Column(String(50))  # Eski alan (geriye dönük uyumluluk)
    tax_office = Column(String(255))  # Vergi Dairesi
    email = Column(String(255), index=True, nullable=True)  # İlk girişte boş olabilir (artık unique DEĞİL)
    phone = Column(String(50), nullable=True)  # İlk girişte boş olabilir
    address = Column(Text)
    
    # Sistem Bilgileri
    role = Column(Enum(UserRole), default=UserRole.MUSTERI)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    ilk_giris_tamamlandi = Column(Boolean, default=False)  # İlk giriş'te profil tamamlandı mı?
    
    # Failed Login Tracking (Brute Force Koruması)
    failed_login_count = Column(Integer, default=0)  # Başarısız login deneme sayısı
    last_failed_login = Column(DateTime, nullable=True)  # Son başarısız login zamanı
    account_locked_until = Column(DateTime, nullable=True)  # Account unlock zamanı (null = locked değil)
    account_locked_reason = Column(String(500), nullable=True)  # Lock nedeni
    
    created_at = Column(DateTime, default=get_turkey_time)
    updated_at = Column(DateTime, default=get_turkey_time, onupdate=get_turkey_time)

    # İlişkiler
    company = relationship("Company", back_populates="users")
    sent_mutabakats = relationship("Mutabakat", foreign_keys="Mutabakat.sender_id", back_populates="sender")
    received_mutabakats = relationship("Mutabakat", foreign_keys="Mutabakat.receiver_id", back_populates="receiver")
    bayiler = relationship("Bayi", back_populates="user", cascade="all, delete-orphan")  # VKN'ye ait bayiler
    logs = relationship("ActivityLog", back_populates="user")

class Mutabakat(Base):
    """Mutabakat Belgesi Modeli - VKN Bazlı (Çoklu Bayi Desteği) - Multi-Company"""
    __tablename__ = "mutabakats"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    mutabakat_no = Column(String(50), unique=True, index=True, nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_vkn = Column(String(11), index=True, nullable=False)  # VKN bazlı arama için
    
    # Dönem bilgileri
    donem_baslangic = Column(DateTime, nullable=False)
    donem_bitis = Column(DateTime, nullable=False)
    
    # Mali bilgiler (Tüm bayilerin toplamı)
    toplam_borc = Column(Float, default=0.0)
    toplam_alacak = Column(Float, default=0.0)
    bakiye = Column(Float, default=0.0)
    toplam_bayi_sayisi = Column(Integer, default=0)  # Bu VKN'ye ait kaç bayi var
    
    # Durum
    durum = Column(Enum(MutabakatDurumu), default=MutabakatDurumu.TASLAK)
    
    # Açıklamalar ve notlar
    aciklama = Column(Text)
    red_nedeni = Column(Text)
    ekstre_talep_edildi = Column(Boolean, default=False)  # Müşteri red ederken ekstre talep etti mi?
    
    # SMS Onay Linki için Token (tek kullanımlık)
    approval_token = Column(String(100), unique=True, index=True)
    token_used = Column(Boolean, default=False)
    token_used_at = Column(DateTime)
    
    # PDF Belgesi
    pdf_file_path = Column(String(255))  # PDF dosya yolu
    
    # Tarihler
    gonderim_tarihi = Column(DateTime)
    onay_tarihi = Column(DateTime)
    red_tarihi = Column(DateTime)
    created_at = Column(DateTime, default=get_turkey_time)
    updated_at = Column(DateTime, default=get_turkey_time, onupdate=get_turkey_time)

    # İlişkiler
    company = relationship("Company", back_populates="mutabakats")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_mutabakats")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_mutabakats")
    items = relationship("MutabakatItem", back_populates="mutabakat", cascade="all, delete-orphan")
    bayi_detaylari = relationship("MutabakatBayiDetay", back_populates="mutabakat", cascade="all, delete-orphan")  # Bayi detayları
    attachments = relationship("MutabakatAttachment", back_populates="mutabakat", cascade="all, delete-orphan")

class MutabakatItem(Base):
    """Mutabakat Kalem Detayları"""
    __tablename__ = "mutabakat_items"

    id = Column(Integer, primary_key=True, index=True)
    mutabakat_id = Column(Integer, ForeignKey("mutabakats.id", ondelete="CASCADE"), nullable=False)
    
    tarih = Column(DateTime, nullable=False)
    belge_no = Column(String(100))
    aciklama = Column(Text)
    borc = Column(Float, default=0.0)
    alacak = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=get_turkey_time)

    # İlişkiler
    mutabakat = relationship("Mutabakat", back_populates="items")

class MutabakatAttachment(Base):
    """Mutabakat Ekleri"""
    __tablename__ = "mutabakat_attachments"

    id = Column(Integer, primary_key=True, index=True)
    mutabakat_id = Column(Integer, ForeignKey("mutabakats.id", ondelete="CASCADE"), nullable=False)
    
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(100))
    file_size = Column(Integer)
    
    uploaded_at = Column(DateTime, default=get_turkey_time)

    # İlişkiler
    mutabakat = relationship("Mutabakat", back_populates="attachments")

class Bayi(Base):
    """Bayi/Cari Kart Modeli - VKN'ye bağlı bayiler"""
    __tablename__ = "bayiler"

    id = Column(Integer, primary_key=True, index=True)
    bayi_kodu = Column(String(50), unique=True, index=True, nullable=False)  # Unique bayi kodu
    vkn_tckn = Column(String(11), index=True, nullable=False)  # Bayi'nin bağlı olduğu VKN/TC
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # VKN sahibi kullanıcı
    
    bayi_adi = Column(String(255), nullable=False)
    vergi_dairesi = Column(String(255))  # Vergi Dairesi
    bakiye = Column(Float, default=0.0)  # Mevcut bakiye (son mutabakattaki bakiye)
    donem = Column(String(7))  # YYYY-MM formatında (örn: 2025-10)
    son_mutabakat_tarihi = Column(DateTime)  # Son mutabakat tarihi (bakiye güncellemesi)
    
    # Adres ve iletişim (opsiyonel)
    adres = Column(Text)
    il = Column(String(100))
    ilce = Column(String(100))
    
    created_at = Column(DateTime, default=get_turkey_time)
    updated_at = Column(DateTime, default=get_turkey_time, onupdate=get_turkey_time)

    # İlişkiler
    user = relationship("User", back_populates="bayiler")

class MutabakatBayiDetay(Base):
    """Mutabakat Bayi Detay - Her mutabakat için bayi bazında bakiye detayları"""
    __tablename__ = "mutabakat_bayi_detay"

    id = Column(Integer, primary_key=True, index=True)
    mutabakat_id = Column(Integer, ForeignKey("mutabakats.id", ondelete="CASCADE"), nullable=False)
    
    bayi_kodu = Column(String(50), nullable=False)
    bayi_adi = Column(String(255), nullable=False)
    bakiye = Column(Float, default=0.0)  # Bu bayinin o dönemdeki bakiyesi
    
    created_at = Column(DateTime, default=get_turkey_time)

    # İlişkiler
    mutabakat = relationship("Mutabakat", back_populates="bayi_detaylari")

class ActivityLog(Base):
    """Aktivite Log Modeli - ISP Bilgili (Yasal Delil için) - Multi-Company"""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)  # Nullable: sistem logları için
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    description = Column(Text)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    # ISP Bilgileri (Yasal Delil için - v2)
    isp = Column(String(255))  # Internet Service Provider
    city = Column(String(255))  # Şehir
    country = Column(String(255))  # Ülke
    organization = Column(String(255))  # ISP Organizasyonu
    
    created_at = Column(DateTime, default=get_turkey_time)

    # İlişkiler
    company = relationship("Company", back_populates="activity_logs")
    user = relationship("User", back_populates="logs")


class FailedLoginAttempt(Base):
    """Başarısız Login Denemeleri - Brute Force Koruması"""
    __tablename__ = "failed_login_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Kullanıcı Bilgisi
    vkn_tckn = Column(String(11), index=True, nullable=False)  # Denenen VKN/TC
    username = Column(String(100), index=True, nullable=True)  # Denenen username (varsa)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Kullanıcı (varsa)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)  # Şirket (varsa)
    
    # Deneme Bilgileri
    ip_address = Column(String(50), index=True, nullable=False)  # Denemenin yapıldığı IP
    user_agent = Column(String(500))
    
    # ISP Bilgileri (Güvenlik analizi için)
    isp = Column(String(255))
    city = Column(String(255))
    country = Column(String(255))
    organization = Column(String(255))
    
    # Hata Bilgisi
    failure_reason = Column(String(500))  # Hata nedeni (wrong password, user not found, account locked, etc.)
    
    # Zaman
    attempted_at = Column(DateTime, default=get_turkey_time, index=True)
    
    # İlişkiler
    user = relationship("User")
    company = relationship("Company")

class KVKKConsent(Base):
    """KVKK Onay Kayıtları - Yasal Uyumluluk - Multi-Company"""
    __tablename__ = "kvkk_consents"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Onay Tipleri
    kvkk_policy_accepted = Column(Boolean, default=False)  # KVKK Politikası
    customer_notice_accepted = Column(Boolean, default=False)  # Müşteri Aydınlatma Metni
    data_retention_accepted = Column(Boolean, default=False)  # Kişisel Veri Saklama ve İmha Politikası
    system_consent_accepted = Column(Boolean, default=False)  # Sistem Kullanım Onayı
    
    # Onay Tarihleri
    kvkk_policy_date = Column(DateTime)
    customer_notice_date = Column(DateTime)
    data_retention_date = Column(DateTime)
    system_consent_date = Column(DateTime)
    
    # ISP Bilgileri (Yasal Delil)
    ip_address = Column(String(50))
    isp = Column(String(255))
    city = Column(String(255))
    country = Column(String(255))
    organization = Column(String(255))
    user_agent = Column(String(500))
    
    # Onay Versiyonları (metin değişirse takip için)
    kvkk_policy_version = Column(String(20), default="1.0")
    customer_notice_version = Column(String(20), default="1.0")
    data_retention_version = Column(String(20), default="1.0")
    system_consent_version = Column(String(20), default="1.0")
    
    created_at = Column(DateTime, default=get_turkey_time)
    updated_at = Column(DateTime, default=get_turkey_time, onupdate=get_turkey_time)

    # İlişkiler
    company = relationship("Company", back_populates="kvkk_consents")
    user = relationship("User")

class KVKKConsentDeletionLog(Base):
    """KVKK Onay Silme Kayıtları - Yasal Delil için Admin İşlemleri"""
    __tablename__ = "kvkk_consent_deletion_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Silinen Onayın Bilgileri (Snapshot)
    original_consent_id = Column(Integer, nullable=False)  # Orijinal consent ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String(100), nullable=False)  # Snapshot
    user_email = Column(String(255))  # Snapshot
    user_full_name = Column(String(255))  # Snapshot
    
    # Silinen Onay Detayları (Snapshot)
    kvkk_policy_accepted = Column(Boolean)
    customer_notice_accepted = Column(Boolean)
    data_retention_accepted = Column(Boolean)
    system_consent_accepted = Column(Boolean)
    
    kvkk_policy_date = Column(DateTime)
    customer_notice_date = Column(DateTime)
    data_retention_date = Column(DateTime)
    system_consent_date = Column(DateTime)
    
    # Orijinal ISP Bilgileri (Onay verildiğinde)
    original_ip_address = Column(String(50))
    original_isp = Column(String(255))
    original_city = Column(String(255))
    original_country = Column(String(255))
    original_organization = Column(String(255))
    original_user_agent = Column(String(500))
    
    # Versiyon Bilgileri
    kvkk_policy_version = Column(String(20))
    customer_notice_version = Column(String(20))
    data_retention_version = Column(String(20))
    system_consent_version = Column(String(20))
    
    # Orijinal oluşturulma tarihi
    original_created_at = Column(DateTime)
    
    # Silme İşlemi Bilgileri
    deleted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Admin
    deleted_by_username = Column(String(100), nullable=False)  # Admin username (snapshot)
    deletion_reason = Column(Text)  # Opsiyonel silme nedeni
    
    # Silme İşleminin ISP Bilgileri
    deletion_ip_address = Column(String(50))
    deletion_isp = Column(String(255))
    deletion_city = Column(String(255))
    deletion_country = Column(String(255))
    deletion_organization = Column(String(255))
    
    deleted_at = Column(DateTime, default=get_turkey_time, nullable=False)
    
    # İlişkiler
    user = relationship("User", foreign_keys=[user_id])
    deleted_by = relationship("User", foreign_keys=[deleted_by_user_id])

