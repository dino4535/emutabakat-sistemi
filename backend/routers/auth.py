from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel
from backend.database import get_db
from backend.models import User
from backend.schemas import UserCreate, UserResponse, Token, UserUpdate, PasswordChange
from backend.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from backend.logger import ActivityLogger
from backend.middleware.rate_limiter import RateLimiter, RateLimitRules
from backend.utils.failed_login_tracker import FailedLoginTracker
from backend.utils.audit_logger import log_login_attempt, create_audit_log
from backend.models import AuditLogAction
import requests

router = APIRouter(prefix="/api/auth", tags=["Kimlik Doğrulama"])


# Multi-Company: Şirket seçim request modeli
class CompanySelectRequest(BaseModel):
    vkn_tckn: str
    company_id: int
    password: str


def get_real_ip_with_isp(request: Request) -> dict:
    """Gerçek public IP adresini ve ISP bilgisini al (Yasal delil için)"""
    # Önce X-Forwarded-For header'ını kontrol et (proxy/load balancer arkasında)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        client_ip = request.headers.get('X-Real-IP')
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    # Eğer localhost ise, gerçek public IP'yi al
    if client_ip in ['127.0.0.1', 'localhost', '::1', 'unknown']:
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=3)
            if response.status_code == 200:
                client_ip = response.json().get('ip')
                print(f"[AUTH-IP] Public IP alındı: {client_ip}")
        except Exception as e:
            print(f"[AUTH-IP] Public IP alınamadı: {e}")
            client_ip = "unknown"
    
    # ISP ve lokasyon bilgisini al
    ip_info = {
        "ip": client_ip,
        "isp": "Bilinmiyor",
        "org": "Bilinmiyor", 
        "city": "Bilinmiyor",
        "country": "Bilinmiyor",
        "region": "Bilinmiyor"
    }
    
    if client_ip != "unknown":
        try:
            response = requests.get(f'http://ip-api.com/json/{client_ip}?fields=status,country,regionName,city,isp,org,query', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    ip_info = {
                        "ip": data.get('query', client_ip),
                        "isp": data.get('isp', 'Bilinmiyor'),
                        "org": data.get('org', 'Bilinmiyor'),
                        "city": data.get('city', 'Bilinmiyor'),
                        "country": data.get('country', 'Bilinmiyor'),
                        "region": data.get('regionName', 'Bilinmiyor')
                    }
                    print(f"[AUTH-IP] ISP: {ip_info['isp']} | Konum: {ip_info['city']}, {ip_info['country']}")
        except Exception as e:
            print(f"[AUTH-IP] ISP bilgisi alınamadı: {e}")
    
    return ip_info

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Yeni kullanıcı kaydı"""
    
    # Email kontrolü
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu email adresi zaten kayıtlı"
        )
    
    # Username kontrolü
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu kullanıcı adı zaten kullanılıyor"
        )
    
    # Yeni kullanıcı oluştur
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        company_name=user.company_name,
        tax_number=user.tax_number,
        phone=user.phone,
        address=user.address,
        role=user.role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Log kaydet (ISP bilgili - Yasal Delil)
    ip_info = get_real_ip_with_isp(request)
    ActivityLogger.log(
        db=db,
        action="KULLANICI_OLUSTUR",
        description=f"Yeni kullanıcı kaydı: {user.email}",
        user_id=db_user.id,
        ip_info=ip_info,
        user_agent=request.headers.get("user-agent", "")
    )
    
    return db_user

@router.post("/login")
@RateLimiter.limit(**RateLimitRules.LOGIN)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Kullanıcı girişi (Multi-Company) - Failed Login Tracking ile"""
    
    # IP ve ISP bilgisi al (failed login tracking için)
    ip_info = get_real_ip_with_isp(request)
    ip_address = ip_info.get("ip", "unknown")
    user_agent = request.headers.get("user-agent", "")
    
    # VKN/TC ile TÜM ŞİRKETLERDEKİ kullanıcıları bul
    users = db.query(User).filter(User.vkn_tckn == form_data.username).all()
    
    if not users:
        # VKN/TC bulunamadıysa, username ile dene (geriye dönük uyumluluk)
        users = db.query(User).filter(User.username == form_data.username).all()
    
    if not users:
        # Failed login kaydı (user bulunamadı)
        FailedLoginTracker.record_failed_login(
            db=db,
            vkn_tckn=form_data.username,
            username=form_data.username,
            user=None,
            ip_address=ip_address,
            user_agent=user_agent,
            isp_info=ip_info,
            failure_reason="User not found"
        )
        
        # Audit log kaydı
        log_login_attempt(
            db=db,
            username=form_data.username,
            success=False,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message="Kullanıcı bulunamadı",
            ip_info=ip_info
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı bulunamadı",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Şifre kontrolü (tüm şirketlerdeki kullanıcılar aynı VKN/şifreye sahip)
    valid_user = None
    for user in users:
        if verify_password(form_data.password, user.hashed_password):
            valid_user = user
            break
    
    if not valid_user:
        # Failed login kaydı (şifre hatalı)
        # İlk kullanıcıyı referans al (hepsi aynı VKN)
        FailedLoginTracker.record_failed_login(
            db=db,
            vkn_tckn=users[0].vkn_tckn,
            username=users[0].username,
            user=users[0],
            ip_address=ip_address,
            user_agent=user_agent,
            isp_info=ip_info,
            failure_reason="Wrong password"
        )
        
        # Audit log kaydı
        log_login_attempt(
            db=db,
            username=users[0].username,
            success=False,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message="Şifre hatalı",
            user=users[0],
            ip_info=ip_info
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Şifre hatalı",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Account locked kontrolü
    is_locked, locked_until = FailedLoginTracker.is_account_locked(valid_user)
    if is_locked:
        remaining_seconds = FailedLoginTracker.get_lockout_time_remaining(valid_user)
        remaining_minutes = int(remaining_seconds / 60)
        
        # Failed login kaydı (account locked)
        FailedLoginTracker.record_failed_login(
            db=db,
            vkn_tckn=valid_user.vkn_tckn,
            username=valid_user.username,
            user=valid_user,
            ip_address=ip_address,
            user_agent=user_agent,
            isp_info=ip_info,
            failure_reason=f"Account locked until {locked_until}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                "error": "Account locked",
                "message": f"Hesabınız çok fazla başarısız giriş denemesi nedeniyle kilitlenmiştir. Lütfen {remaining_minutes} dakika sonra tekrar deneyin.",
                "locked_until": locked_until.isoformat(),
                "retry_after": remaining_seconds,
                "reason": valid_user.account_locked_reason
            },
            headers={"Retry-After": str(remaining_seconds)}
        )
    
    # Aktif kullanıcı kontrolü
    active_users = [u for u in users if u.is_active]
    if not active_users:
        # Failed login kaydı (inactive user)
        FailedLoginTracker.record_failed_login(
            db=db,
            vkn_tckn=valid_user.vkn_tckn,
            username=valid_user.username,
            user=valid_user,
            ip_address=ip_address,
            user_agent=user_agent,
            isp_info=ip_info,
            failure_reason="User inactive"
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hiçbir şirketteki kullanıcı aktif değil"
        )
    
    # DURUM 1: Kullanıcı birden fazla şirkette kayıtlı → Şirket seçim ekranı
    if len(active_users) > 1:
        companies_list = []
        for u in active_users:
            companies_list.append({
                "company_id": u.company_id,
                "company_name": u.company.company_name,
                "full_company_name": u.company.full_company_name,
                "logo_path": u.company.logo_path,
                "bayi_kodu": u.bayi_kodu,
                "username": u.username,
                "user_id": u.id
            })
        
        return {
            "requires_company_selection": True,
            "companies": companies_list,
            "vkn_tckn": valid_user.vkn_tckn
        }
    
    # DURUM 2: Kullanıcı tek şirkette kayıtlı → Direkt login
    user = active_users[0]
    
    # Başarılı login: Failed login counter'ı sıfırla
    FailedLoginTracker.reset_failed_login_counter(db, user)
    
    # Token oluştur (company_id dahil)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "company_id": user.company_id  # Multi-company için
        },
        expires_delta=access_token_expires
    )
    
    # Log kaydet (ISP bilgili - Yasal Delil)
    ActivityLogger.log(
        db=db,
        action="login",
        description=f"Kullanici girisi yapti: {user.username} (Company: {user.company.company_name})",
        user_id=user.id,
        ip_info=ip_info,
        user_agent=request.headers.get("user-agent", ""),
        company_id=user.company_id  # Multi-company için
    )
    
    # Audit log kaydı (başarılı login)
    log_login_attempt(
        db=db,
        username=user.username,
        success=True,
        ip_address=ip_address,
        user_agent=user_agent,
        user=user,
        ip_info=ip_info
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "requires_company_selection": False,
        "ilk_giris_tamamlandi": user.ilk_giris_tamamlandi if hasattr(user, 'ilk_giris_tamamlandi') else True,
        "vkn_tckn": user.vkn_tckn if hasattr(user, 'vkn_tckn') else None,
        "company_id": user.company_id,
        "company_name": user.company.company_name,
        "bayi_kodu": user.bayi_kodu
    }

@router.post("/login/select-company")
@RateLimiter.limit(**RateLimitRules.LOGIN)
async def login_select_company(
    request: Request,
    data: CompanySelectRequest,
    db: Session = Depends(get_db)
):
    """Kullanıcı şirket seçimi yaptıktan sonra login (Multi-Company) - Failed Login Tracking ile"""
    
    # IP ve ISP bilgisi al
    ip_info = get_real_ip_with_isp(request)
    ip_address = ip_info.get("ip", "unknown")
    user_agent = request.headers.get("user-agent", "")
    
    # Belirtilen şirketteki kullanıcıyı bul
    user = db.query(User).filter(
        User.vkn_tckn == data.vkn_tckn,
        User.company_id == data.company_id
    ).first()
    
    if not user:
        # Failed login kaydı
        FailedLoginTracker.record_failed_login(
            db=db,
            vkn_tckn=data.vkn_tckn,
            username=None,
            user=None,
            ip_address=ip_address,
            user_agent=user_agent,
            isp_info=ip_info,
            failure_reason="User not found in selected company"
        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bu şirkette bulunamadı"
        )
    
    # Şifre kontrolü
    if not verify_password(data.password, user.hashed_password):
        # Failed login kaydı
        FailedLoginTracker.record_failed_login(
            db=db,
            vkn_tckn=user.vkn_tckn,
            username=user.username,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            isp_info=ip_info,
            failure_reason="Wrong password (company select)"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Şifre hatalı",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Account locked kontrolü
    is_locked, locked_until = FailedLoginTracker.is_account_locked(user)
    if is_locked:
        remaining_seconds = FailedLoginTracker.get_lockout_time_remaining(user)
        remaining_minutes = int(remaining_seconds / 60)
        
        # Failed login kaydı
        FailedLoginTracker.record_failed_login(
            db=db,
            vkn_tckn=user.vkn_tckn,
            username=user.username,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            isp_info=ip_info,
            failure_reason=f"Account locked (company select) until {locked_until}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                "error": "Account locked",
                "message": f"Hesabınız çok fazla başarısız giriş denemesi nedeniyle kilitlenmiştir. Lütfen {remaining_minutes} dakika sonra tekrar deneyin.",
                "locked_until": locked_until.isoformat(),
                "retry_after": remaining_seconds,
                "reason": user.account_locked_reason
            },
            headers={"Retry-After": str(remaining_seconds)}
        )
    
    if not user.is_active:
        # Failed login kaydı
        FailedLoginTracker.record_failed_login(
            db=db,
            vkn_tckn=user.vkn_tckn,
            username=user.username,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            isp_info=ip_info,
            failure_reason="User inactive (company select)"
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kullanıcı aktif değil"
        )
    
    # Başarılı login: Failed login counter'ı sıfırla
    FailedLoginTracker.reset_failed_login_counter(db, user)
    
    # Token oluştur (company_id dahil)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "company_id": user.company_id
        },
        expires_delta=access_token_expires
    )
    
    # Log kaydet
    ActivityLogger.log(
        db=db,
        action="login_company_selection",
        description=f"Sirket secimi ile giris: {user.username} (Company: {user.company.company_name})",
        user_id=user.id,
        ip_info=ip_info,
        user_agent=request.headers.get("user-agent", ""),
        company_id=user.company_id
    )
    
    # Audit log kaydı (başarılı login - şirket seçimi)
    log_login_attempt(
        db=db,
        username=user.username,
        success=True,
        ip_address=ip_address,
        user_agent=user_agent,
        user=user,
        ip_info=ip_info
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "requires_company_selection": False,
        "ilk_giris_tamamlandi": user.ilk_giris_tamamlandi if hasattr(user, 'ilk_giris_tamamlandi') else True,
        "vkn_tckn": user.vkn_tckn,
        "company_id": user.company_id,
        "company_name": user.company.company_name,
        "bayi_kodu": user.bayi_kodu
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Mevcut kullanıcı bilgilerini getir"""
    # Şirket bilgilerini al
    from backend.models import Company
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    
    # Role'u string olarak döndür
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "company_name": current_user.company_name,
        "tax_number": current_user.tax_number,
        "tax_office": current_user.tax_office if hasattr(current_user, 'tax_office') else None,
        "phone": current_user.phone,
        "address": current_user.address,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "vkn_tckn": current_user.vkn_tckn if hasattr(current_user, 'vkn_tckn') else None,
        "ilk_giris_tamamlandi": current_user.ilk_giris_tamamlandi if hasattr(current_user, 'ilk_giris_tamamlandi') else True,
        "company_logo": company.logo_path if company else None,
        "created_at": current_user.created_at
    }
    return user_dict

@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Kullanıcı çıkışı"""
    
    # Log kaydet (ISP bilgili - Yasal Delil)
    ip_info = get_real_ip_with_isp(request)
    ActivityLogger.log_logout(
        db,
        current_user.id,
        ip_info
    )
    
    return {"message": "Başarıyla çıkış yapıldı"}

@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_data: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Kullanıcı profil bilgilerini güncelle"""
    
    # İlk giriş kontrolü - Email ve telefon zorunlu
    is_first_login = current_user.ilk_giris_tamamlandi == False
    if is_first_login:
        if not profile_data.email or '@' not in profile_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="İlk girişte geçerli bir e-posta adresi zorunludur"
            )
        if not profile_data.phone or len(profile_data.phone) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="İlk girişte geçerli bir telefon numarası zorunludur"
            )
        # İlk giriş tamamlandı olarak işaretle
        if profile_data.ilk_giris_tamamlandi is None:
            profile_data.ilk_giris_tamamlandi = True
    
    # Email değişikliği kontrolü
    if profile_data.email and profile_data.email != current_user.email:
        existing_user = db.query(User).filter(
            User.email == profile_data.email,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu email adresi başka bir kullanıcı tarafından kullanılıyor"
            )
    
    # Profil bilgilerini güncelle
    for field, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    # Log kaydet (ISP bilgili - Yasal Delil)
    ip_info = get_real_ip_with_isp(request)
    ActivityLogger.log(
        db=db,
        action="profile_updated",
        description="Kullanıcı profil bilgilerini güncelledi",
        user_id=current_user.id,
        ip_info=ip_info,
        user_agent=request.headers.get("user-agent", "")
    )
    
    return current_user

@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Kullanıcı şifresini değiştir"""
    
    # Mevcut şifreyi doğrula
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mevcut şifre hatalı"
        )
    
    # Yeni şifreyi hashle ve güncelle
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    # Log kaydet (ISP bilgili - Yasal Delil)
    ip_info = get_real_ip_with_isp(request)
    ActivityLogger.log(
        db=db,
        action="password_changed",
        description="Kullanıcı şifresini değiştirdi",
        user_id=current_user.id,
        ip_info=ip_info,
        user_agent=request.headers.get("user-agent", "")
    )
    
    return {"message": "Şifre başarıyla değiştirildi"}

@router.post("/complete-profile", response_model=UserResponse)
def complete_profile(
    phone: str,
    email: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    İlk giriş sonrası profil tamamlama
    Telefon ve email zorunlu
    """
    
    # Email kontrolü
    if email:
        existing_user = db.query(User).filter(
            User.email == email,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu email adresi başka bir kullanıcı tarafından kullanılıyor"
            )
    
    # Telefon ve email güncelle
    current_user.phone = phone
    current_user.email = email
    current_user.ilk_giris_tamamlandi = True
    
    db.commit()
    db.refresh(current_user)
    
    # Log kaydet (ISP bilgili - Yasal Delil)
    ip_info = get_real_ip_with_isp(request)
    ActivityLogger.log(
        db=db,
        action="profile_completed",
        description="İlk giriş profil tamamlandı",
        user_id=current_user.id,
        ip_info=ip_info,
        user_agent=request.headers.get("user-agent", "")
    )
    
    # User response döndür
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "company_name": current_user.company_name,
        "tax_number": current_user.tax_number,
        "phone": current_user.phone,
        "address": current_user.address,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "vkn_tckn": current_user.vkn_tckn if hasattr(current_user, 'vkn_tckn') else None,
        "ilk_giris_tamamlandi": current_user.ilk_giris_tamamlandi,
        "created_at": current_user.created_at
    }
    return user_dict

