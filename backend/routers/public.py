"""
Public API endpoints (authentication gerektirmez)
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Mutabakat, MutabakatDurumu, Company
from backend.schemas import MutabakatResponse
from backend.utils.tokens import verify_approval_token, mark_token_as_used
from backend.logger import ActivityLogger
from backend.sms import sms_service
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
import requests

def get_real_ip(request: Request) -> str:
    """Gerçek public IP adresini al (ISP IP)"""
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    client_ip = request.client.host if request.client else "unknown"
    
    if client_ip in ['127.0.0.1', 'localhost', '::1']:
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=3)
            if response.status_code == 200:
                return response.json().get('ip')
        except:
            pass
    
    return client_ip

router = APIRouter(prefix="/api/public", tags=["Public"])

class TokenApprovalRequest(BaseModel):
    """Token ile onay/red talebi"""
    action: str  # "approve" veya "reject"
    red_nedeni: Optional[str] = None

@router.get("/mutabakat/{token}", response_model=MutabakatResponse)
def get_mutabakat_by_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Token ile mutabakatı getir (public endpoint - authentication yok)
    
    Args:
        token: Onay token'ı
        db: Database session
        
    Returns:
        MutabakatResponse: Mutabakat detayları
    """
    # Token'ı doğrula
    mutabakat = verify_approval_token(db, token)
    
    if not mutabakat:
        raise HTTPException(
            status_code=404,
            detail="Geçersiz veya kullanılmış link. Bu link artık geçerli değil."
        )
    
    # Sadece gönderilmiş mutabakatlar görülebilir
    if mutabakat.durum != MutabakatDurumu.GONDERILDI:
        raise HTTPException(
            status_code=400,
            detail="Bu mutabakat zaten işleme alınmış."
        )
    
    return mutabakat

@router.post("/mutabakat/{token}/action")
def approve_or_reject_by_token(
    token: str,
    request_data: TokenApprovalRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Token ile mutabakatı onayla veya reddet (public endpoint)
    
    Args:
        token: Onay token'ı
        request_data: Aksiyon ve red nedeni
        request: Request objesi
        db: Database session
        
    Returns:
        dict: İşlem sonucu
    """
    # Token'ı doğrula
    mutabakat = verify_approval_token(db, token)
    
    if not mutabakat:
        raise HTTPException(
            status_code=404,
            detail="Geçersiz veya kullanılmış link. Bu link artık geçerli değil."
        )
    
    # Sadece gönderilmiş mutabakatlar işlenebilir
    if mutabakat.durum != MutabakatDurumu.GONDERILDI:
        raise HTTPException(
            status_code=400,
            detail="Bu mutabakat zaten işleme alınmış."
        )
    
    action = request_data.action.lower()
    
    if action == "approve":
        # Onayla
        mutabakat.durum = MutabakatDurumu.ONAYLANDI
        mutabakat.onay_tarihi = datetime.utcnow()
        
        # PDF lazy generation: istendiğinde oluşturulacak (hız için)
        
        # Token'ı kullanıldı olarak işaretle
        mark_token_as_used(db, token)
        
        db.commit()
        db.refresh(mutabakat)
        
        # Log kaydet - SMS üzerinden onay
        ActivityLogger.log_activity(
            db=db,
            user_id=mutabakat.receiver_id,
            action="MUTABAKAT_ONAYLA_SMS",
            description=f"Mutabakat SMS linki üzerinden onaylandı: {mutabakat.mutabakat_no}",
            ip=request.client.host if request.client else "unknown"
        )
        
        # Gönderen şirketin email adresine bildirim gönder
        sender = mutabakat.sender
        sender_company = db.query(Company).filter(Company.id == sender.company_id).first() if sender else None
        
        if sender_company and sender_company.notification_email:
            try:
                from backend.utils.email_service import email_service
                
                receiver_name = mutabakat.receiver.company_name or mutabakat.receiver.full_name or mutabakat.receiver.username
                email_service.send_mutabakat_approved(
                    to_email=sender_company.notification_email,
                    company_name=sender_company.company_name,
                    customer_name=receiver_name,
                    mutabakat_no=mutabakat.mutabakat_no,
                    donem_baslangic=mutabakat.donem_baslangic,
                    donem_bitis=mutabakat.donem_bitis,
                    toplam_borc=mutabakat.toplam_borc,
                    toplam_alacak=mutabakat.toplam_alacak,
                    bakiye=mutabakat.bakiye,
                    onay_tarihi=mutabakat.onay_tarihi
                )
            except Exception as e:
                ActivityLogger.log_error(
                    db, 
                    f"Email gönderme hatası: {e}", 
                    mutabakat.receiver_id, 
                    request.client.host if request.client else "unknown"
                )
        
        return {
            "success": True,
            "message": "Mutabakat başarıyla onaylandı!",
            "mutabakat_no": mutabakat.mutabakat_no
        }
    
    elif action == "reject":
        # Red et
        if not request_data.red_nedeni:
            raise HTTPException(
                status_code=400,
                detail="Red nedeni belirtilmelidir."
            )
        
        mutabakat.durum = MutabakatDurumu.REDDEDILDI
        mutabakat.red_nedeni = request_data.red_nedeni
        mutabakat.red_tarihi = datetime.utcnow()
        
        # PDF lazy generation: istendiğinde oluşturulacak (hız için)
        
        # Token'ı kullanıldı olarak işaretle
        mark_token_as_used(db, token)
        
        db.commit()
        db.refresh(mutabakat)
        
        # Log kaydet - SMS üzerinden red
        ActivityLogger.log_activity(
            db=db,
            user_id=mutabakat.receiver_id,
            action="MUTABAKAT_REDDET_SMS",
            description=f"Mutabakat SMS linki üzerinden reddedildi: {mutabakat.mutabakat_no} - Neden: {request_data.red_nedeni}",
            ip=request.client.host if request.client else "unknown"
        )
        
        # Gönderen şirketin email adresine bildirim gönder
        sender = mutabakat.sender
        sender_company = db.query(Company).filter(Company.id == sender.company_id).first() if sender else None
        
        if sender_company and sender_company.notification_email:
            try:
                from backend.utils.email_service import email_service
                
                receiver_name = mutabakat.receiver.company_name or mutabakat.receiver.full_name or mutabakat.receiver.username
                email_service.send_mutabakat_rejected(
                    to_email=sender_company.notification_email,
                    company_name=sender_company.company_name,
                    customer_name=receiver_name,
                    mutabakat_no=mutabakat.mutabakat_no,
                    donem_baslangic=mutabakat.donem_baslangic,
                    donem_bitis=mutabakat.donem_bitis,
                    toplam_borc=mutabakat.toplam_borc,
                    toplam_alacak=mutabakat.toplam_alacak,
                    bakiye=mutabakat.bakiye,
                    red_nedeni=request_data.red_nedeni,
                    red_tarihi=mutabakat.red_tarihi
                )
            except Exception as e:
                ActivityLogger.log_error(
                    db, 
                    f"Email gönderme hatası: {e}", 
                    mutabakat.receiver_id, 
                    request.client.host if request.client else "unknown"
                )
        
        return {
            "success": True,
            "message": "Mutabakat reddedildi.",
            "mutabakat_no": mutabakat.mutabakat_no
        }
    
    else:
        raise HTTPException(
            status_code=400,
            detail="Geçersiz aksiyon. 'approve' veya 'reject' olmalıdır."
        )

