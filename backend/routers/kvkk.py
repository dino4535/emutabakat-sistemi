"""
KVKK (Kişisel Verilerin Korunması Kanunu) Router
Kullanıcı onayları ve KVKK metinleri
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, KVKKConsent, UserRole, KVKKConsentDeletionLog, Company
from backend.schemas import KVKKConsentCreate, KVKKConsentResponse, KVKKTextsResponse
from backend.auth import get_current_active_user
from datetime import datetime
import pytz
import requests

# KVKK metinlerini import et
from backend.kvkk_constants import (
    KVKK_POLICY_TEXT, KVKK_POLICY_TITLE, KVKK_POLICY_SUMMARY, KVKK_POLICY_VERSION,
    CUSTOMER_NOTICE_TEXT, CUSTOMER_NOTICE_TITLE, CUSTOMER_NOTICE_SUMMARY, CUSTOMER_NOTICE_VERSION,
    DATA_RETENTION_POLICY_TEXT, DATA_RETENTION_TITLE, DATA_RETENTION_SUMMARY, DATA_RETENTION_VERSION,
    SYSTEM_CONSENT_TEXT, SYSTEM_CONSENT_TITLE, SYSTEM_CONSENT_SUMMARY, SYSTEM_CONSENT_VERSION
)

router = APIRouter(prefix="/api/kvkk", tags=["KVKK"])

# Türkiye saat dilimi
TURKEY_TZ = pytz.timezone('Europe/Istanbul')

def get_turkey_time():
    """Türkiye saatini döndür (UTC+3)"""
    return datetime.now(TURKEY_TZ)

def get_real_ip_with_isp(request: Request) -> dict:
    """Gerçek public IP adresini ve ISP bilgisini al (Yasal delil için)"""
    # Önce X-Forwarded-For header'ını kontrol et
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        client_ip = request.headers.get('X-Real-IP')
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    # Localhost ise gerçek public IP'yi al
    if client_ip in ['127.0.0.1', 'localhost', '::1']:
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=3)
            if response.status_code == 200:
                public_ip = response.json().get('ip')
                print(f"[IP] Public IP alındı: {public_ip}")
                client_ip = public_ip
        except Exception as e:
            print(f"[IP] Public IP alınamadı: {e}")
    
    # ISP bilgisini al
    isp_info = {
        'ip': client_ip,
        'isp': None,
        'city': None,
        'country': None,
        'org': None
    }
    
    try:
        response = requests.get(f'http://ip-api.com/json/{client_ip}', timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                isp_info['isp'] = data.get('isp')
                isp_info['city'] = data.get('city')
                isp_info['country'] = data.get('country')
                isp_info['org'] = data.get('org')
                
                print(f"[IP] IP Adresi: {isp_info['ip']}")
                print(f"[IP] ISP: {isp_info['isp']}")
                print(f"[IP] Şehir: {isp_info['city']}, {data.get('regionName')}")
                print(f"[IP] Ülke: {isp_info['country']}")
                print(f"[IP] Organizasyon: {data.get('org')}")
    except Exception as e:
        print(f"[IP] ISP bilgisi alınamadı: {e}")
    
    return isp_info

@router.get("/texts", response_model=KVKKTextsResponse)
def get_kvkk_texts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """KVKK metinlerini döndür (Multi-Company: Her şirket kendi metinleri)"""
    
    # Kullanıcının şirketini al
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    
    # Company'den metinleri al, yoksa fallback to constants
    return {
        "kvkk_policy": {
            "title": KVKK_POLICY_TITLE,
            "summary": KVKK_POLICY_SUMMARY,
            "content": company.kvkk_policy_text if company and company.kvkk_policy_text else KVKK_POLICY_TEXT,
            "version": company.kvkk_policy_version if company and company.kvkk_policy_version else KVKK_POLICY_VERSION
        },
        "customer_notice": {
            "title": CUSTOMER_NOTICE_TITLE,
            "summary": CUSTOMER_NOTICE_SUMMARY,
            "content": company.customer_notice_text if company and company.customer_notice_text else CUSTOMER_NOTICE_TEXT,
            "version": company.customer_notice_version if company and company.customer_notice_version else CUSTOMER_NOTICE_VERSION
        },
        "data_retention": {
            "title": DATA_RETENTION_TITLE,
            "summary": DATA_RETENTION_SUMMARY,
            "content": company.data_retention_policy_text if company and company.data_retention_policy_text else DATA_RETENTION_POLICY_TEXT,
            "version": company.data_retention_version if company and company.data_retention_version else DATA_RETENTION_VERSION
        },
        "system_consent": {
            "title": SYSTEM_CONSENT_TITLE,
            "summary": SYSTEM_CONSENT_SUMMARY,
            "content": company.system_consent_text if company and company.system_consent_text else SYSTEM_CONSENT_TEXT,
            "version": company.system_consent_version if company and company.system_consent_version else SYSTEM_CONSENT_VERSION
        }
    }

@router.get("/consent/status", response_model=KVKKConsentResponse)
def get_kvkk_consent_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Kullanıcının KVKK onay durumunu döndür"""
    consent = db.query(KVKKConsent).filter(
        KVKKConsent.user_id == current_user.id
    ).first()
    
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KVKK onayı bulunamadı"
        )
    
    return consent

@router.post("/consent", response_model=KVKKConsentResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_kvkk_consent(
    consent_data: KVKKConsentCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """KVKK onaylarını kaydet veya güncelle (Multi-Company)"""
    
    # IP ve ISP bilgisini al
    ip_info = get_real_ip_with_isp(request)
    user_agent = request.headers.get('user-agent', '')
    
    # Mevcut onay kaydını kontrol et (SADECE KENDİ ŞİRKETİNDE)
    consent = db.query(KVKKConsent).filter(
        KVKKConsent.user_id == current_user.id,
        KVKKConsent.company_id == current_user.company_id  # Multi-Company Filter
    ).first()
    
    now = get_turkey_time()
    
    if consent:
        # Güncelleme
        if consent_data.kvkk_policy_accepted and not consent.kvkk_policy_accepted:
            consent.kvkk_policy_accepted = True
            consent.kvkk_policy_date = now
            consent.kvkk_policy_version = KVKK_POLICY_VERSION
            
        if consent_data.customer_notice_accepted and not consent.customer_notice_accepted:
            consent.customer_notice_accepted = True
            consent.customer_notice_date = now
            consent.customer_notice_version = CUSTOMER_NOTICE_VERSION
            
        if consent_data.data_retention_accepted and not consent.data_retention_accepted:
            consent.data_retention_accepted = True
            consent.data_retention_date = now
            consent.data_retention_version = DATA_RETENTION_VERSION
            
        if consent_data.system_consent_accepted and not consent.system_consent_accepted:
            consent.system_consent_accepted = True
            consent.system_consent_date = now
            consent.system_consent_version = SYSTEM_CONSENT_VERSION
        
        # ISP bilgilerini güncelle (en son onay bilgisi)
        consent.ip_address = ip_info['ip']
        consent.isp = ip_info['isp']
        consent.city = ip_info['city']
        consent.country = ip_info['country']
        consent.organization = ip_info['org']
        consent.user_agent = user_agent
        
    else:
        # Yeni kayıt (Multi-Company: company_id ekle)
        consent = KVKKConsent(
            company_id=current_user.company_id,  # Multi-Company: Şirket ID'si
            user_id=current_user.id,
            kvkk_policy_accepted=consent_data.kvkk_policy_accepted,
            customer_notice_accepted=consent_data.customer_notice_accepted,
            data_retention_accepted=consent_data.data_retention_accepted,
            system_consent_accepted=consent_data.system_consent_accepted,
            kvkk_policy_date=now if consent_data.kvkk_policy_accepted else None,
            customer_notice_date=now if consent_data.customer_notice_accepted else None,
            data_retention_date=now if consent_data.data_retention_accepted else None,
            system_consent_date=now if consent_data.system_consent_accepted else None,
            kvkk_policy_version=KVKK_POLICY_VERSION,
            customer_notice_version=CUSTOMER_NOTICE_VERSION,
            data_retention_version=DATA_RETENTION_VERSION,
            system_consent_version=SYSTEM_CONSENT_VERSION,
            ip_address=ip_info['ip'],
            isp=ip_info['isp'],
            city=ip_info['city'],
            country=ip_info['country'],
            organization=ip_info['org'],
            user_agent=user_agent
        )
        db.add(consent)
    
    db.commit()
    db.refresh(consent)
    
    # Log kaydet
    print(f"[KVKK] User {current_user.id} ({current_user.username}) onay verdi:")
    print(f"  - KVKK Politikası: {consent.kvkk_policy_accepted}")
    print(f"  - Müşteri Aydınlatma: {consent.customer_notice_accepted}")
    print(f"  - Veri Saklama: {consent.data_retention_accepted}")
    print(f"  - Sistem Onayı: {consent.system_consent_accepted}")
    print(f"  - IP: {ip_info['ip']} ({ip_info['isp']})")
    
    return consent

@router.get("/consent/check")
def check_kvkk_consent(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Kullanıcının tüm KVKK onaylarını verip vermediğini kontrol et (Multi-Company)"""
    consent = db.query(KVKKConsent).filter(
        KVKKConsent.user_id == current_user.id,
        KVKKConsent.company_id == current_user.company_id  # Multi-Company Filter
    ).first()
    
    if not consent:
        return {
            "all_consents_given": False,
            "missing_consents": ["kvkk_policy", "customer_notice", "data_retention", "system_consent"]
        }
    
    missing = []
    if not consent.kvkk_policy_accepted:
        missing.append("kvkk_policy")
    if not consent.customer_notice_accepted:
        missing.append("customer_notice")
    if not consent.data_retention_accepted:
        missing.append("data_retention")
    if not consent.system_consent_accepted:
        missing.append("system_consent")
    
    return {
        "all_consents_given": len(missing) == 0,
        "missing_consents": missing
    }

# ============================================================================
# ADMIN ENDPOINTS - KVKK Yönetimi
# ============================================================================

@router.get("/admin/consent/{user_id}", response_model=KVKKConsentResponse)
def get_user_kvkk_consent(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Admin: Belirli bir kullanıcının KVKK onaylarını görüntüle - Multi-Company"""
    # Admin ve Company Admin erişebilir
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    
    # Kullanıcıyı kontrol et
    user_query = db.query(User).filter(User.id == user_id)
    
    # Company admin ise sadece kendi şirketinin kullanıcılarını görebilir
    if current_user.role == UserRole.COMPANY_ADMIN:
        user_query = user_query.filter(User.company_id == current_user.company_id)
    
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı veya erişim yetkiniz yok"
        )
    
    # KVKK onaylarını getir
    consent = db.query(KVKKConsent).filter(
        KVKKConsent.user_id == user_id
    ).first()
    
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu kullanıcının KVKK onayı bulunamadı"
        )
    
    return consent

@router.delete("/admin/consent/{user_id}")
def delete_user_kvkk_consent(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Admin: Belirli bir kullanıcının KVKK onaylarını sil - Multi-Company (kullanıcı tekrar onay vermek zorunda kalır)"""
    # Admin ve Company Admin erişebilir
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    
    # Kullanıcıyı kontrol et
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
    
    # KVKK onaylarını bul
    consent = db.query(KVKKConsent).filter(
        KVKKConsent.user_id == user_id
    ).first()
    
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu kullanıcının KVKK onayı bulunamadı"
        )
    
    # Silme işleminin IP ve ISP bilgilerini al
    deletion_ip_info = get_real_ip_with_isp(request)
    
    # Silinen onayı log tablosuna kaydet (Yasal delil)
    deletion_log = KVKKConsentDeletionLog(
        original_consent_id=consent.id,
        user_id=user.id,
        username=user.username,
        user_email=user.email,
        user_full_name=user.full_name,
        
        # Onay detayları (snapshot)
        kvkk_policy_accepted=consent.kvkk_policy_accepted,
        customer_notice_accepted=consent.customer_notice_accepted,
        data_retention_accepted=consent.data_retention_accepted,
        system_consent_accepted=consent.system_consent_accepted,
        
        kvkk_policy_date=consent.kvkk_policy_date,
        customer_notice_date=consent.customer_notice_date,
        data_retention_date=consent.data_retention_date,
        system_consent_date=consent.system_consent_date,
        
        # Orijinal ISP bilgileri (onay verildiğinde)
        original_ip_address=consent.ip_address,
        original_isp=consent.isp,
        original_city=consent.city,
        original_country=consent.country,
        original_organization=consent.organization,
        original_user_agent=consent.user_agent,
        
        # Versiyon bilgileri
        kvkk_policy_version=consent.kvkk_policy_version,
        customer_notice_version=consent.customer_notice_version,
        data_retention_version=consent.data_retention_version,
        system_consent_version=consent.system_consent_version,
        
        original_created_at=consent.created_at,
        
        # Silme işlemi bilgileri
        deleted_by_user_id=current_user.id,
        deleted_by_username=current_user.username,
        deletion_reason=None,  # İleride frontend'den alınabilir
        
        # Silme işleminin ISP bilgileri
        deletion_ip_address=deletion_ip_info['ip'],
        deletion_isp=deletion_ip_info['isp'],
        deletion_city=deletion_ip_info['city'],
        deletion_country=deletion_ip_info['country'],
        deletion_organization=deletion_ip_info['org']
    )
    
    db.add(deletion_log)
    
    # Orijinal onayı sil
    db.delete(consent)
    db.commit()
    
    # Console log kaydet
    print(f"\n[KVKK ADMIN] ========================================")
    print(f"[KVKK ADMIN] KVKK Onayı Silindi (Yasal Delil Kaydedildi)")
    print(f"[KVKK ADMIN] ========================================")
    print(f"[KVKK ADMIN] Silinen Kullanıcı: {user.username} (ID: {user_id})")
    print(f"[KVKK ADMIN] Silen Admin: {current_user.username} (ID: {current_user.id})")
    print(f"[KVKK ADMIN] Admin IP: {deletion_ip_info['ip']} ({deletion_ip_info['isp']})")
    print(f"[KVKK ADMIN] Log ID: {deletion_log.id}")
    print(f"[KVKK ADMIN] ========================================\n")
    
    return {
        "message": "KVKK onayları başarıyla silindi. Kullanıcı tekrar onay vermek zorunda kalacak.",
        "user_id": user_id,
        "username": user.username,
        "deletion_log_id": deletion_log.id,
        "deleted_by": current_user.username
    }

