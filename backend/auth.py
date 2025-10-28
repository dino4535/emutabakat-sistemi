from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Şifre doğrulama - Bcrypt ile"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Şifre hashleme - Bcrypt ile"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """JWT token oluşturma"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Mevcut kullanıcıyı token'dan al (Multi-Company)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulama başarısız",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        company_id: int = payload.get("company_id")  # JWT'den company_id al
        
        if username is None or company_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Kullanıcıyı username + company_id ile bul (aynı username farklı şirketlerde olabilir)
    user = db.query(User).filter(
        User.username == username,
        User.company_id == company_id
    ).first()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Kullanıcı aktif değil")
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Aktif kullanıcıyı al"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Kullanıcı aktif değil")
    return current_user

def require_role(allowed_roles: list):
    """Rol kontrolü için decorator"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için yetkiniz yok"
            )
        return current_user
    return role_checker

def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Sistem admini veya şirket admini kontrolü
    Sistem admini (admin): Tüm şirketlere erişebilir
    Şirket admini (company_admin): Sadece kendi şirketine erişebilir
    """
    from backend.models import UserRole
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    return current_user

def get_system_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Sadece sistem admini kontrolü (tüm şirketleri yönetebilir)
    """
    from backend.models import UserRole
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için sistem admin yetkisi gerekli"
        )
    return current_user

def require_admin_or_owner(resource_company_id: int):
    """
    Sistem admini veya kaynağın sahibi kontrolü
    
    Args:
        resource_company_id: Kontrol edilecek kaynağın company_id'si
    """
    def checker(current_user: User = Depends(get_current_active_user)) -> User:
        from backend.models import UserRole
        
        # Sistem admini her zaman erişebilir
        if current_user.role == UserRole.ADMIN:
            return current_user
        
        # Şirket admini sadece kendi şirketine erişebilir
        if current_user.role == UserRole.COMPANY_ADMIN and current_user.company_id == resource_company_id:
            return current_user
        
        # Diğer kullanıcılar erişemez
        if current_user.company_id != resource_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu kaynağa erişim yetkiniz yok"
            )
        
        return current_user
    return checker

