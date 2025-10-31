"""
Token yönetimi için yardımcı fonksiyonlar
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
import os
from backend.models import Mutabakat

def generate_approval_token() -> str:
    """
    Mutabakat onay linki için benzersiz token oluştur
    
    Returns:
        str: Güvenli, URL-safe token (32 karakter)
    """
    return secrets.token_urlsafe(32)

def create_approval_token(db: Session, mutabakat_id: int) -> Optional[str]:
    """
    Mutabakat için onay token'ı oluştur ve kaydet
    
    Args:
        db: Database session
        mutabakat_id: Mutabakat ID
        
    Returns:
        str: Oluşturulan token veya None
    """
    mutabakat = db.query(Mutabakat).filter(Mutabakat.id == mutabakat_id).first()
    
    if not mutabakat:
        return None
    
    # Yeni token oluştur
    token = generate_approval_token()
    
    # Token'ı kaydet
    mutabakat.approval_token = token
    mutabakat.token_used = False
    mutabakat.token_used_at = None
    
    db.commit()
    db.refresh(mutabakat)
    
    return token

def verify_approval_token(db: Session, token: str) -> Optional[Mutabakat]:
    """
    Token'ı doğrula ve mutabakatı getir
    
    Args:
        db: Database session
        token: Onay token'ı
        
    Returns:
        Mutabakat: Token geçerliyse mutabakat objesi, değilse None
    """
    if not token:
        return None
    
    # Token'ı ara
    mutabakat = db.query(Mutabakat).filter(
        Mutabakat.approval_token == token
    ).first()
    
    if not mutabakat:
        return None
    
    # Token kullanıldı mı kontrol et
    if mutabakat.token_used:
        return None
    
    return mutabakat

def mark_token_as_used(db: Session, token: str) -> bool:
    """
    Token'ı kullanıldı olarak işaretle
    
    Args:
        db: Database session
        token: Onay token'ı
        
    Returns:
        bool: Başarılı ise True
    """
    mutabakat = db.query(Mutabakat).filter(
        Mutabakat.approval_token == token
    ).first()
    
    if not mutabakat:
        return False
    
    mutabakat.token_used = True
    mutabakat.token_used_at = datetime.utcnow()
    
    db.commit()
    
    return True

def get_approval_link(token: str, base_url: str = "http://localhost:3000") -> str:
    """
    Token için tam onay linki oluştur
    
    Args:
        token: Onay token'ı
        base_url: Frontend base URL
        
    Returns:
        str: Tam onay linki
    """
    # Ortam değişkeninden FRONTEND_URL al; yoksa parametre ile gelen base_url'i kullan
    env_base = os.getenv("FRONTEND_URL")
    final_base = (env_base or base_url).rstrip('/')
    return f"{final_base}/mutabakat/onay/{token}"

