"""
Public API endpoints (authentication gerektirmez)
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Mutabakat, MutabakatDurumu, Company, ActivityLog
from backend.schemas import MutabakatResponse
from backend.utils.tokens import verify_approval_token, mark_token_as_used
from backend.logger import ActivityLogger, logger
from backend.sms import sms_service
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List, Dict
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

def get_real_ip_with_isp(request: Request) -> dict:
    """Gerçek public IP adresini ve ISP bilgisini al"""
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        client_ip = request.headers.get('X-Real-IP')
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    if client_ip in ['127.0.0.1', 'localhost', '::1', 'unknown']:
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=3)
            if response.status_code == 200:
                client_ip = response.json().get('ip')
        except:
            pass
    
    ip_info = {
        "ip": client_ip,
        "isp": "Bilinmiyor",
        "org": "Bilinmiyor",
        "city": "Bilinmiyor",
        "country": "Bilinmiyor"
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
                        "country": data.get('country', 'Bilinmiyor')
                    }
        except:
            pass
    
    return ip_info

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
        # KVKK onay kontrolü (token'daki mutabakatın alıcısı için)
        from backend.models import KVKKConsent, User
        receiver = mutabakat.receiver
        if not receiver:
            raise HTTPException(status_code=404, detail="Alıcı bulunamadı")
        consent = db.query(KVKKConsent).filter(
            KVKKConsent.user_id == receiver.id,
            KVKKConsent.company_id == mutabakat.company_id
        ).first()
        missing_consents = []
        if not consent or not consent.kvkk_policy_accepted:
            missing_consents.append("kvkk_policy")
        if not consent or not consent.customer_notice_accepted:
            missing_consents.append("customer_notice")
        if not consent or not consent.data_retention_accepted:
            missing_consents.append("data_retention")
        if not consent or not consent.system_consent_accepted:
            missing_consents.append("system_consent")
        if missing_consents:
            # KVKK onayı eksik - frontend'e özel response dön
            return {
                "success": False,
                "requires_kvkk_consent": True,
                "message": "Mutabakatı onaylamadan önce KVKK onaylarını tamamlamanız gerekmektedir.",
                "missing_consents": missing_consents,
                "mutabakat": {
                    "id": mutabakat.id,
                    "mutabakat_no": mutabakat.mutabakat_no,
                    "donem_baslangic": mutabakat.donem_baslangic.isoformat() if mutabakat.donem_baslangic else None,
                    "donem_bitis": mutabakat.donem_bitis.isoformat() if mutabakat.donem_bitis else None,
                    "toplam_borc": float(mutabakat.toplam_borc) if mutabakat.toplam_borc else 0.0,
                    "toplam_alacak": float(mutabakat.toplam_alacak) if mutabakat.toplam_alacak else 0.0,
                    "bakiye": float(mutabakat.bakiye) if mutabakat.bakiye else 0.0
                }
            }
        # Onayla
        mutabakat.durum = MutabakatDurumu.ONAYLANDI
        mutabakat.onay_tarihi = datetime.utcnow()
        
        # PDF lazy generation: istendiğinde oluşturulacak (hız için)
        
        # Token'ı kullanıldı olarak işaretle
        mark_token_as_used(db, token)
        
        # SMS Log'u güncelle (token kullanıldı)
        from backend.models import SMSVerificationLog
        sms_log = db.query(SMSVerificationLog).filter(
            SMSVerificationLog.approval_token == token
        ).first()
        if sms_log:
            sms_log.token_used = True
            sms_log.token_used_at = datetime.utcnow()
        
        db.commit()
        db.refresh(mutabakat)
        
        # IP ve ISP bilgilerini al
        try:
            ip_info = get_real_ip_with_isp(request)
        except:
            ip_info = {
                "ip": request.client.host if request.client else "unknown",
                "isp": "Bilinmiyor",
                "city": "Bilinmiyor",
                "country": "Bilinmiyor",
                "org": "Bilinmiyor"
            }
        
        # Log kaydet - SMS üzerinden onay (ISP bilgili)
        from backend.logger import log_activity
        log_activity(
            db=db,
            action="MUTABAKAT_ONAYLA_SMS",
            description=f"Mutabakat SMS linki üzerinden onaylandı: {mutabakat.mutabakat_no}",
            user_id=mutabakat.receiver_id,
            ip_info=ip_info,
            company_id=mutabakat.company_id
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
        
        # Push notification gönder (gönderene)
        if sender:
            try:
                from backend.utils.push_notifications import send_mutabakat_approved_push
                receiver_name = mutabakat.receiver.company_name or mutabakat.receiver.full_name or mutabakat.receiver.username
                send_mutabakat_approved_push(
                    db=db,
                    sender_id=sender.id,
                    mutabakat_no=mutabakat.mutabakat_no,
                    receiver_name=receiver_name,
                    amount=mutabakat.bakiye
                )
            except Exception as e:
                logger.error(f"[PUSH] Mutabakat onay push hatası: {e}")
        
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
        
        # IP ve ISP bilgilerini al
        try:
            ip_info = get_real_ip_with_isp(request)
        except:
            ip_info = {
                "ip": request.client.host if request.client else "unknown",
                "isp": "Bilinmiyor",
                "city": "Bilinmiyor",
                "country": "Bilinmiyor",
                "org": "Bilinmiyor"
            }
        
        # Log kaydet - SMS üzerinden red (ISP bilgili)
        from backend.logger import log_activity
        log_activity(
            db=db,
            action="MUTABAKAT_REDDET_SMS",
            description=f"Mutabakat SMS linki üzerinden reddedildi: {mutabakat.mutabakat_no} - Neden: {request_data.red_nedeni}",
            user_id=mutabakat.receiver_id,
            ip_info=ip_info,
            company_id=mutabakat.company_id
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
        
        # Push notification gönder (gönderene)
        if sender:
            try:
                from backend.utils.push_notifications import send_mutabakat_rejected_push
                receiver_name = mutabakat.receiver.company_name or mutabakat.receiver.full_name or mutabakat.receiver.username
                send_mutabakat_rejected_push(
                    db=db,
                    sender_id=sender.id,
                    mutabakat_no=mutabakat.mutabakat_no,
                    receiver_name=receiver_name,
                    reason=request_data.red_nedeni,
                    amount=mutabakat.bakiye
                )
            except Exception as e:
                logger.error(f"[PUSH] Mutabakat red push hatası: {e}")
        
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


class PublicKVKKConsentRequest(BaseModel):
    """Public KVKK Onay Talebi (Token ile)"""
    kvkk_policy_accepted: bool
    customer_notice_accepted: bool
    data_retention_accepted: bool
    system_consent_accepted: bool

@router.post("/mutabakat/{token}/kvkk-consent")
def submit_kvkk_consent_by_token(
    token: str,
    consent_data: PublicKVKKConsentRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Token ile KVKK onayı gönder (public endpoint - SMS linki üzerinden)
    
    Args:
        token: Onay token'ı
        consent_data: KVKK onay bilgileri
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
    
    # Alıcıyı bul
    receiver = mutabakat.receiver
    if not receiver:
        raise HTTPException(status_code=404, detail="Alıcı bulunamadı")
    
    # IP ve ISP bilgisini al
    try:
        ip_info = get_real_ip_with_isp(request)
    except:
        ip_info = {
            "ip": request.client.host if request.client else "unknown",
            "isp": "Bilinmiyor",
            "city": "Bilinmiyor",
            "country": "Bilinmiyor",
            "org": "Bilinmiyor"
        }
    
    user_agent = request.headers.get('user-agent', '')
    
    # KVKK onayını kaydet veya güncelle
    from backend.models import KVKKConsent, get_turkey_time
    from backend.routers.kvkk import (
        KVKK_POLICY_VERSION, CUSTOMER_NOTICE_VERSION,
        DATA_RETENTION_VERSION, SYSTEM_CONSENT_VERSION
    )
    
    now = get_turkey_time()
    
    consent = db.query(KVKKConsent).filter(
        KVKKConsent.user_id == receiver.id,
        KVKKConsent.company_id == mutabakat.company_id
    ).first()
    
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
        
        # ISP bilgilerini güncelle
        consent.ip_address = ip_info['ip']
        consent.isp = ip_info['isp']
        consent.city = ip_info['city']
        consent.country = ip_info['country']
        consent.organization = ip_info.get('org', 'Bilinmiyor')
        consent.user_agent = user_agent
    else:
        # Yeni kayıt
        consent = KVKKConsent(
            company_id=mutabakat.company_id,
            user_id=receiver.id,
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
            organization=ip_info.get('org', 'Bilinmiyor'),
            user_agent=user_agent
        )
        db.add(consent)
    
    db.commit()
    db.refresh(consent)
    
    # Log kaydet (ISP bilgili)
    from backend.logger import log_activity
    log_activity(
        db=db,
        action="KVKK_CONSENT_GIVEN_PUBLIC",
        description=f"KVKK onayı SMS linki üzerinden verildi (Token: {token[:12]}...)",
        user_id=receiver.id,
        ip_info=ip_info,
        company_id=mutabakat.company_id,
        user_agent=user_agent
    )
    
    return {
        "success": True,
        "message": "KVKK onayları başarıyla kaydedildi. Şimdi mutabakatı onaylayabilirsiniz.",
        "all_consents_given": (
            consent.kvkk_policy_accepted and
            consent.customer_notice_accepted and
            consent.data_retention_accepted and
            consent.system_consent_accepted
        )
    }

@router.get("/mutabakat/{token}/kvkk-status")
def get_kvkk_status_by_token(
    token: str,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Token ile KVKK onay durumunu getir (public endpoint)
    """
    # Token'ı doğrula
    mutabakat = verify_approval_token(db, token)
    if not mutabakat:
        raise HTTPException(
            status_code=404,
            detail="Geçersiz veya kullanılmış link. Bu link artık geçerli değil."
        )
    # Alıcıyı bul
    receiver = mutabakat.receiver
    if not receiver:
        raise HTTPException(status_code=404, detail="Alıcı bulunamadı")
    # KVKK durumu
    from backend.models import KVKKConsent
    consent = db.query(KVKKConsent).filter(
        KVKKConsent.user_id == receiver.id,
        KVKKConsent.company_id == mutabakat.company_id
    ).first()
    missing_consents = []
    if not consent or not consent.kvkk_policy_accepted:
        missing_consents.append("kvkk_policy")
    if not consent or not consent.customer_notice_accepted:
        missing_consents.append("customer_notice")
    if not consent or not consent.data_retention_accepted:
        missing_consents.append("data_retention")
    if not consent or not consent.system_consent_accepted:
        missing_consents.append("system_consent")
    return {
        "requires_kvkk_consent": len(missing_consents) > 0,
        "missing_consents": missing_consents
    }


@router.get("/mutabakat/{token}/kvkk-texts")
def get_kvkk_texts_by_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Token ile KVKK metinlerini getir (public endpoint - SMS linki üzerinden)
    
    Args:
        token: Onay token'ı
        db: Database session
        
    Returns:
        dict: KVKK metinleri
    """
    # Token'ı doğrula
    mutabakat = verify_approval_token(db, token)
    
    if not mutabakat:
        raise HTTPException(
            status_code=404,
            detail="Geçersiz veya kullanılmış link. Bu link artık geçerli değil."
        )
    
    # Şirket bilgisini al
    company = db.query(Company).filter(Company.id == mutabakat.company_id).first()
    
    # KVKK metinlerini import et
    from backend.kvkk_constants import (
        KVKK_POLICY_TEXT, KVKK_POLICY_TITLE, KVKK_POLICY_SUMMARY, KVKK_POLICY_VERSION,
        CUSTOMER_NOTICE_TEXT, CUSTOMER_NOTICE_TITLE, CUSTOMER_NOTICE_SUMMARY, CUSTOMER_NOTICE_VERSION,
        DATA_RETENTION_POLICY_TEXT, DATA_RETENTION_TITLE, DATA_RETENTION_SUMMARY, DATA_RETENTION_VERSION,
        SYSTEM_CONSENT_TEXT, SYSTEM_CONSENT_TITLE, SYSTEM_CONSENT_SUMMARY, SYSTEM_CONSENT_VERSION
    )
    
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


@router.get("/mutabakat/verify/{mutabakat_no}")
def verify_mutabakat_by_no(
    mutabakat_no: str,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Mutabakat no ile mutabakat bilgilerini getir (public endpoint - QR kod için)
    
    Args:
        mutabakat_no: Mutabakat numarası
        db: Database session
        
    Returns:
        dict: Mutabakat özet bilgileri ve işlem logları
    """
    # Mutabakatı bul
    mutabakat = db.query(Mutabakat).filter(
        Mutabakat.mutabakat_no == mutabakat_no
    ).first()
    
    if not mutabakat:
        raise HTTPException(
            status_code=404,
            detail="Mutabakat bulunamadı"
        )
    
    # Şirket bilgisi
    company = db.query(Company).filter(Company.id == mutabakat.company_id).first()
    
    # Activity logları - mutabakat oluşturma ve onaylama/red logları
    logs = db.query(ActivityLog).filter(
        ActivityLog.description.like(f"%{mutabakat_no}%")
    ).order_by(ActivityLog.created_at.asc()).all()
    
    # Logları formatla
    formatted_logs = []
    for log in logs:
        formatted_logs.append({
            "action": log.action,
            "description": log.description,
            "user_id": log.user_id,
            "username": log.user.username if log.user else "Sistem",
            "full_name": log.user.full_name if log.user else "Sistem",
            "ip_address": log.ip_address,
            "isp": log.isp,
            "city": log.city,
            "country": log.country,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })
    
    # Bayi detaylarını al
    bayi_detaylari = []
    if mutabakat.bayi_detaylari:
        for detay in mutabakat.bayi_detaylari:
            bayi_detaylari.append({
                "bayi_kodu": detay.bayi_kodu,
                "bayi_adi": detay.bayi_adi,
                "bakiye": float(detay.bakiye) if detay.bakiye else 0.0
            })
    
    # Mutabakat özeti
    summary = {
        "mutabakat_no": mutabakat.mutabakat_no,
        "company_name": company.company_name if company else "Bilinmiyor",
        "company_vkn": company.vkn if company else None,
        "company_logo": company.logo_path if company and company.logo_path else None,
        "durum": mutabakat.durum.value if mutabakat.durum else "Bilinmiyor",
        "donem_baslangic": mutabakat.donem_baslangic.isoformat() if mutabakat.donem_baslangic else None,
        "donem_bitis": mutabakat.donem_bitis.isoformat() if mutabakat.donem_bitis else None,
        "toplam_borc": float(mutabakat.toplam_borc) if mutabakat.toplam_borc else 0.0,
        "toplam_alacak": float(mutabakat.toplam_alacak) if mutabakat.toplam_alacak else 0.0,
        "bakiye": float(mutabakat.bakiye) if mutabakat.bakiye else 0.0,
        "toplam_bayi_sayisi": mutabakat.toplam_bayi_sayisi or 0,
        "sender_name": mutabakat.sender.company_name or mutabakat.sender.full_name if mutabakat.sender else "Bilinmiyor",
        "receiver_name": mutabakat.receiver.company_name or mutabakat.receiver.full_name if mutabakat.receiver else "Bilinmiyor",
        "receiver_vkn": mutabakat.receiver_vkn,
        "created_at": mutabakat.created_at.isoformat() if mutabakat.created_at else None,
        "onay_tarihi": mutabakat.onay_tarihi.isoformat() if mutabakat.onay_tarihi else None,
        "red_tarihi": mutabakat.red_tarihi.isoformat() if mutabakat.red_tarihi else None,
        "red_nedeni": mutabakat.red_nedeni,
        "aciklama": mutabakat.aciklama,
        "bayi_detaylari": bayi_detaylari
    }
    
    return {
        "success": True,
        "mutabakat": summary,
        "logs": formatted_logs
    }

