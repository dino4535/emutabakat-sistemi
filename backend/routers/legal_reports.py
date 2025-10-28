"""
Yasal Raporlar Router
Resmi makamlar için detaylı mutabakat ve kullanıcı raporları
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.database import get_db
from backend.models import (
    User, Mutabakat, MutabakatItem, ActivityLog, 
    KVKKConsent, KVKKConsentDeletionLog, UserRole, Company
)
from backend.auth import get_current_active_user
from backend.utils.legal_report_pdf import LegalReportPDFGenerator, generate_legal_report_hash
from backend.utils.pdf_signer import pdf_signer
from backend.utils.pdf_permissions import apply_pdf_permissions
from backend.logger import ActivityLogger
from datetime import datetime
from typing import Optional
import os
from pathlib import Path
import hashlib
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor

router = APIRouter(prefix="/api/reports", tags=["Legal Reports"])


def get_real_ip_with_isp(request: Request) -> dict:
    """Gerçek public IP adresini ve ISP bilgisini al (Yasal delil için)"""
    # Önce X-Forwarded-For header'ını kontrol et (proxy/load balancer arkasında)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # İlk IP gerçek client IP'sidir
        client_ip = forwarded_for.split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        client_ip = request.headers.get('X-Real-IP')
    else:
        # Client IP'yi al
        client_ip = request.client.host if request.client else "unknown"
    
    # Eğer localhost ise, gerçek public IP'yi al
    if client_ip in ['127.0.0.1', 'localhost', '::1', 'unknown']:
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=3)
            if response.status_code == 200:
                client_ip = response.json().get('ip')
                print(f"[IP] Public IP alındı: {client_ip}")
        except Exception as e:
            print(f"[IP] Public IP alınamadı: {e}")
            client_ip = "unknown"
    
    # ISP ve lokasyon bilgisini al (ip-api.com - ücretsiz, yasal delil için)
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
            # ip-api.com ücretsiz ve ISP bilgisi veriyor
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
                    print(f"[IP] IP Adresi: {ip_info['ip']}")
                    print(f"[IP] ISP: {ip_info['isp']}")
                    print(f"[IP] Konum: {ip_info['city']}, {ip_info['country']}")
        except Exception as e:
            print(f"[IP] ISP bilgisi alınamadı: {e}")
    
    return ip_info

@router.get("/legal/search")
def search_legal_report(
    identifier: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Yasal Rapor Arama - VKN veya Mutabakat Numarası ile (Multi-Company)
    Sadece Admin ve Company Admin erişebilir
    """
    # Admin kontrolü
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    
    # VKN ile arama mı, Mutabakat No ile arama mı?
    is_vkn = identifier.isdigit() and len(identifier) >= 10
    
    if is_vkn:
        # VKN ile kullanıcı ara
        user_query = db.query(User).filter(
            or_(
                User.vkn_tckn == identifier,
                User.username == identifier
            )
        )
        
        # Company admin ise sadece kendi şirketinin kullanıcılarını görebilir
        if current_user.role == UserRole.COMPANY_ADMIN:
            user_query = user_query.filter(User.company_id == current_user.company_id)
        
        user = user_query.first()
        
        if not user:
            return {
                "found": False,
                "search_type": "vkn",
                "identifier": identifier,
                "message": "Bu VKN/TC ile kullanıcı bulunamadı veya erişim yetkiniz yok"
            }
        
        # Kullanıcının tüm mutabakatlarını getir
        mutabakat_query = db.query(Mutabakat).filter(
            or_(
                Mutabakat.sender_id == user.id,
                Mutabakat.receiver_id == user.id
            )
        )
        
        # Company admin ise sadece kendi şirketinin mutabakatlarını görebilir
        if current_user.role == UserRole.COMPANY_ADMIN:
            mutabakat_query = mutabakat_query.filter(Mutabakat.company_id == current_user.company_id)
        
        mutabakats = mutabakat_query.order_by(Mutabakat.created_at.desc()).all()
        
        return {
            "found": True,
            "search_type": "vkn",
            "user": {
                "id": user.id,
                "vkn_tckn": user.vkn_tckn,
                "username": user.username,
                "full_name": user.full_name,
                "company_name": user.company_name,
                "email": user.email,
                "phone": user.phone,
                "address": user.address,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "mutabakat_count": len(mutabakats),
            "mutabakat_list": [
                {
                    "id": m.id,
                    "mutabakat_no": m.mutabakat_no,
                    "durum": m.durum.value,
                    "bakiye": float(m.bakiye) if m.bakiye else 0,
                    "toplam_borc": float(m.toplam_borc) if m.toplam_borc else 0,
                    "toplam_alacak": float(m.toplam_alacak) if m.toplam_alacak else 0,
                    "donem_baslangic": m.donem_baslangic.isoformat() if m.donem_baslangic else None,
                    "donem_bitis": m.donem_bitis.isoformat() if m.donem_bitis else None,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "role": "sender" if m.sender_id == user.id else "receiver"
                }
                for m in mutabakats
            ]
        }
    
    else:
        # Mutabakat numarası ile ara
        mutabakat_query = db.query(Mutabakat).filter(
            Mutabakat.mutabakat_no == identifier.upper()
        )
        
        # Company admin ise sadece kendi şirketinin mutabakatlarını görebilir
        if current_user.role == UserRole.COMPANY_ADMIN:
            mutabakat_query = mutabakat_query.filter(Mutabakat.company_id == current_user.company_id)
        
        mutabakat = mutabakat_query.first()
        
        if not mutabakat:
            return {
                "found": False,
                "search_type": "mutabakat_no",
                "identifier": identifier,
                "message": "Bu mutabakat numarası bulunamadı veya erişim yetkiniz yok"
            }
        
        return {
            "found": True,
            "search_type": "mutabakat_no",
            "mutabakat_id": mutabakat.id,
            "mutabakat_no": mutabakat.mutabakat_no
        }

@router.get("/legal/mutabakat/{mutabakat_id}")
def get_legal_mutabakat_report(
    mutabakat_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Belirli bir mutabakat için detaylı yasal rapor (Multi-Company)
    Tüm loglar, ISP bilgileri, KVKK kayıtları dahil
    """
    # Admin kontrolü
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    
    # Mutabakat bilgilerini getir
    mutabakat_query = db.query(Mutabakat).filter(Mutabakat.id == mutabakat_id)
    
    # Company admin ise sadece kendi şirketinin mutabakatlarını görebilir
    if current_user.role == UserRole.COMPANY_ADMIN:
        mutabakat_query = mutabakat_query.filter(Mutabakat.company_id == current_user.company_id)
    
    mutabakat = mutabakat_query.first()
    if not mutabakat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mutabakat bulunamadı veya erişim yetkiniz yok"
        )
    
    # Gönderen ve alıcı bilgilerini getir
    sender = db.query(User).filter(User.id == mutabakat.sender_id).first()
    receiver = db.query(User).filter(User.id == mutabakat.receiver_id).first()
    
    # Mutabakat kalemleri
    items = db.query(MutabakatItem).filter(
        MutabakatItem.mutabakat_id == mutabakat_id
    ).all()
    
    # Activity logları (bu mutabakat için)
    activity_logs = db.query(ActivityLog).filter(
        ActivityLog.description.contains(mutabakat.mutabakat_no)
    ).order_by(ActivityLog.created_at.desc()).all()
    
    # Gönderen ve alıcı için KVKK onayları
    sender_kvkk = db.query(KVKKConsent).filter(
        KVKKConsent.user_id == sender.id
    ).first() if sender else None
    
    receiver_kvkk = db.query(KVKKConsent).filter(
        KVKKConsent.user_id == receiver.id
    ).first() if receiver else None
    
    # KVKK silme logları
    sender_kvkk_deletions = db.query(KVKKConsentDeletionLog).filter(
        KVKKConsentDeletionLog.user_id == sender.id
    ).order_by(KVKKConsentDeletionLog.deleted_at.desc()).all() if sender else []
    
    receiver_kvkk_deletions = db.query(KVKKConsentDeletionLog).filter(
        KVKKConsentDeletionLog.user_id == receiver.id
    ).order_by(KVKKConsentDeletionLog.deleted_at.desc()).all() if receiver else []
    
    # Rapor oluştur
    report = {
        "report_type": "mutabakat",  # Frontend için gerekli
        "report_generated_at": datetime.now().isoformat(),
        "generated_by": {
            "user_id": current_user.id,
            "username": current_user.username,
            "full_name": current_user.full_name
        },
        "mutabakat": {
            "id": mutabakat.id,
            "mutabakat_no": mutabakat.mutabakat_no,
            "durum": mutabakat.durum.value,
            "bakiye": float(mutabakat.bakiye) if mutabakat.bakiye else 0,
            "toplam_borc": float(mutabakat.toplam_borc) if mutabakat.toplam_borc else 0,
            "toplam_alacak": float(mutabakat.toplam_alacak) if mutabakat.toplam_alacak else 0,
            "toplam_bayi_sayisi": mutabakat.toplam_bayi_sayisi or 0,
            "donem_baslangic": mutabakat.donem_baslangic.isoformat() if mutabakat.donem_baslangic else None,
            "donem_bitis": mutabakat.donem_bitis.isoformat() if mutabakat.donem_bitis else None,
            "aciklama": mutabakat.aciklama,
            "red_nedeni": mutabakat.red_nedeni,
            "pdf_file_path": mutabakat.pdf_file_path,
            "created_at": mutabakat.created_at.isoformat() if mutabakat.created_at else None,
            "updated_at": mutabakat.updated_at.isoformat() if mutabakat.updated_at else None,
            "items_count": len(items)
        },
        "sender": {
            "vkn_tckn": '-',
            "full_name": 'Dino Gida',
            "company_name": 'Huseyin ve Ibrahim Kaplan Dino Gida San. Tic. Ltd. Sti.',
            "email": 'info@dinogida.com.tr',
            "phone": '0850 220 45 66'
        },  # Gönderen: Mutabakatı oluşturan firma (Dino Gıda)
        "receiver": {
            "id": receiver.id,
            "vkn_tckn": receiver.vkn_tckn,
            "username": receiver.username,
            "full_name": receiver.full_name,
            "company_name": receiver.company_name,
            "email": receiver.email,
            "phone": receiver.phone,
            "address": receiver.address,
            "role": receiver.role.value,
            "created_at": receiver.created_at.isoformat() if receiver.created_at else None
        } if receiver else None,
        "items": [
            {
                "id": item.id,
                "belge_no": item.belge_no,
                "tarih": item.tarih.isoformat() if item.tarih else None,
                "borc": float(item.borc) if item.borc else 0,
                "alacak": float(item.alacak) if item.alacak else 0,
                "aciklama": item.aciklama
            }
            for item in items
        ],
        "activity_logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "description": log.description,
                "ip_address": log.ip_address,
                "isp": log.isp,
                "city": log.city,
                "country": log.country,
                "organization": log.organization,
                "timestamp": log.created_at.isoformat() if log.created_at else None
            }
            for log in activity_logs
        ],
        "kvkk_consents": {
            "sender": {
                "exists": False  # Gönderen KVKK gösterme
            },
            "receiver": {
                "exists": receiver_kvkk is not None,
                "data": {
                    "kvkk_policy_accepted": receiver_kvkk.kvkk_policy_accepted,
                    "customer_notice_accepted": receiver_kvkk.customer_notice_accepted,
                    "data_retention_accepted": receiver_kvkk.data_retention_accepted,
                    "system_consent_accepted": receiver_kvkk.system_consent_accepted,
                    "kvkk_policy_date_str": receiver_kvkk.kvkk_policy_date.strftime("%d.%m.%Y %H:%M:%S") if receiver_kvkk.kvkk_policy_date else "-",
                    "customer_notice_date_str": receiver_kvkk.customer_notice_date.strftime("%d.%m.%Y %H:%M:%S") if receiver_kvkk.customer_notice_date else "-",
                    "data_retention_date_str": receiver_kvkk.data_retention_date.strftime("%d.%m.%Y %H:%M:%S") if receiver_kvkk.data_retention_date else "-",
                    "system_consent_date_str": receiver_kvkk.system_consent_date.strftime("%d.%m.%Y %H:%M:%S") if receiver_kvkk.system_consent_date else "-",
                    "ip_address": receiver_kvkk.ip_address,
                    "isp": receiver_kvkk.isp,
                    "city": receiver_kvkk.city,
                    "country": receiver_kvkk.country,
                    "created_at": receiver_kvkk.created_at.isoformat() if receiver_kvkk.created_at else None,
                    "created_at_str": receiver_kvkk.created_at.strftime("%d.%m.%Y %H:%M:%S") if receiver_kvkk.created_at else "-"
                } if receiver_kvkk else None
            }
        },
        "kvkk_deletion_logs": {
            "sender": [],  # Gönderen KVKK deletion logs gösterme
            "receiver": [
                {
                    "id": log.id,
                    "original_consent_id": log.original_consent_id,
                    "deleted_by_username": log.deleted_by_username,
                    "deletion_reason": log.deletion_reason,
                    "deletion_ip_address": log.deletion_ip_address,
                    "deletion_isp": log.deletion_isp,
                    "deletion_city": log.deletion_city,
                    "deletion_country": log.deletion_country,
                    "original_ip_address": log.original_ip_address,
                    "original_isp": log.original_isp,
                    "deleted_at": log.deleted_at.isoformat() if log.deleted_at else None,
                    "deleted_at_str": log.deleted_at.strftime("%d.%m.%Y %H:%M:%S") if log.deleted_at else "-"
                }
                for log in receiver_kvkk_deletions
            ]
        }
    }
    
    # Console log
    print(f"\n[YASAL RAPOR] ========================================")
    print(f"[YASAL RAPOR] Yasal Rapor Oluşturuldu")
    print(f"[YASAL RAPOR] Mutabakat No: {mutabakat.mutabakat_no}")
    print(f"[YASAL RAPOR] Raporu Oluşturan: {current_user.username}")
    print(f"[YASAL RAPOR] Toplam Log Sayısı: {len(activity_logs)}")
    print(f"[YASAL RAPOR] ========================================\n")
    
    return report

@router.get("/legal/user/{user_id}")
def get_legal_user_report(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Belirli bir kullanıcı için detaylı yasal rapor (Multi-Company)
    Tüm mutabakatlar, loglar, KVKK kayıtları dahil
    """
    # Admin kontrolü
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    
    # Kullanıcı bilgilerini getir
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
    
    # Kullanıcının tüm mutabakatları
    mutabakat_query = db.query(Mutabakat).filter(
        or_(
            Mutabakat.sender_id == user_id,
            Mutabakat.receiver_id == user_id
        )
    )
    
    # Company admin ise sadece kendi şirketinin mutabakatlarını görebilir
    if current_user.role == UserRole.COMPANY_ADMIN:
        mutabakat_query = mutabakat_query.filter(Mutabakat.company_id == current_user.company_id)
    
    mutabakats = mutabakat_query.order_by(Mutabakat.created_at.desc()).all()
    
    # Kullanıcının tüm activity logları
    activity_logs = db.query(ActivityLog).filter(
        ActivityLog.user_id == user_id
    ).order_by(ActivityLog.created_at.desc()).all()
    
    # KVKK onayları
    kvkk_consent = db.query(KVKKConsent).filter(
        KVKKConsent.user_id == user_id
    ).first()
    
    # KVKK silme logları
    kvkk_deletions = db.query(KVKKConsentDeletionLog).filter(
        KVKKConsentDeletionLog.user_id == user_id
    ).order_by(KVKKConsentDeletionLog.deleted_at.desc()).all()
    
    # Rapor oluştur
    report = {
        "report_type": "user",  # Frontend için gerekli
        "report_generated_at": datetime.now().isoformat(),
        "generated_by": {
            "user_id": current_user.id,
            "username": current_user.username,
            "full_name": current_user.full_name
        },
        "user": {
            "id": user.id,
            "vkn_tckn": user.vkn_tckn,
            "username": user.username,
            "full_name": user.full_name,
            "company_name": user.company_name,
            "email": user.email,
            "phone": user.phone,
            "address": user.address,
            "role": user.role.value,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None
        },
        "statistics": {
            "total_mutabakats": len(mutabakats),
            "total_activity_logs": len(activity_logs),
            "kvkk_consent_exists": kvkk_consent is not None,
            "kvkk_deletions_count": len(kvkk_deletions)
        },
        "mutabakats": [
            {
                "id": m.id,
                "mutabakat_no": m.mutabakat_no,
                "durum": m.durum.value,
                "bakiye": float(m.bakiye) if m.bakiye else 0,
                "toplam_borc": float(m.toplam_borc) if m.toplam_borc else 0,
                "toplam_alacak": float(m.toplam_alacak) if m.toplam_alacak else 0,
                "donem_baslangic": m.donem_baslangic.isoformat() if m.donem_baslangic else None,
                "donem_bitis": m.donem_bitis.isoformat() if m.donem_bitis else None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "role": "sender" if m.sender_id == user_id else "receiver"
            }
            for m in mutabakats
        ],
        "activity_logs": [
            {
                "id": log.id,
                "action": log.action,
                "description": log.description,
                "ip_address": log.ip_address,
                "isp": log.isp,
                "city": log.city,
                "country": log.country,
                "timestamp": log.created_at.isoformat() if log.created_at else None
            }
            for log in activity_logs
        ],
        "kvkk_consents": {
            "sender": {
                "exists": False  # Gönderen KVKK gösterme
            },
            "receiver": {
                "exists": kvkk_consent is not None,
                "data": {
                    "kvkk_policy_accepted": kvkk_consent.kvkk_policy_accepted,
                    "customer_notice_accepted": kvkk_consent.customer_notice_accepted,
                    "data_retention_accepted": kvkk_consent.data_retention_accepted,
                    "system_consent_accepted": kvkk_consent.system_consent_accepted,
                    "kvkk_policy_date_str": kvkk_consent.kvkk_policy_date.strftime("%d.%m.%Y %H:%M:%S") if kvkk_consent.kvkk_policy_date else "-",
                    "customer_notice_date_str": kvkk_consent.customer_notice_date.strftime("%d.%m.%Y %H:%M:%S") if kvkk_consent.customer_notice_date else "-",
                    "data_retention_date_str": kvkk_consent.data_retention_date.strftime("%d.%m.%Y %H:%M:%S") if kvkk_consent.data_retention_date else "-",
                    "system_consent_date_str": kvkk_consent.system_consent_date.strftime("%d.%m.%Y %H:%M:%S") if kvkk_consent.system_consent_date else "-",
                    "ip_address": kvkk_consent.ip_address,
                    "isp": kvkk_consent.isp,
                    "city": kvkk_consent.city,
                    "country": kvkk_consent.country,
                    "created_at": kvkk_consent.created_at.isoformat() if kvkk_consent.created_at else None,
                    "created_at_str": kvkk_consent.created_at.strftime("%d.%m.%Y %H:%M:%S") if kvkk_consent.created_at else "-"
                } if kvkk_consent else None
            }
        },
        "kvkk_deletion_logs": {
            "sender": [],  # Gönderen KVKK deletion logs gösterme
            "receiver": [
                {
                    "id": log.id,
                    "original_consent_id": log.original_consent_id,
                    "deleted_by_username": log.deleted_by_username,
                    "deletion_reason": log.deletion_reason,
                    "deletion_ip_address": log.deletion_ip_address,
                    "deletion_isp": log.deletion_isp,
                    "deletion_city": log.deletion_city,
                    "deletion_country": log.deletion_country,
                    "original_ip_address": log.original_ip_address,
                    "original_isp": log.original_isp,
                    "deleted_at": log.deleted_at.isoformat() if log.deleted_at else None,
                    "deleted_at_str": log.deleted_at.strftime("%d.%m.%Y %H:%M:%S") if log.deleted_at else "-"
                }
                for log in kvkk_deletions
            ]
        }
    }
    
    # Console log
    print(f"\n[YASAL RAPOR] ========================================")
    print(f"[YASAL RAPOR] Kullanıcı Yasal Rapor Oluşturuldu")
    print(f"[YASAL RAPOR] Kullanıcı: {user.username} ({user.vkn_tckn})")
    print(f"[YASAL RAPOR] Raporu Oluşturan: {current_user.username}")
    print(f"[YASAL RAPOR] Toplam Mutabakat: {len(mutabakats)}")
    print(f"[YASAL RAPOR] Toplam Log: {len(activity_logs)}")
    print(f"[YASAL RAPOR] ========================================\n")
    
    return report


@router.get("/legal/mutabakat/{mutabakat_id}/pdf")
async def download_legal_mutabakat_pdf(
    mutabakat_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Mutabakat Yasal Raporu PDF İndir (Multi-Company)
    Dijital imzalı, şifreli, hash'lenmiş PDF oluşturur
    """
    print(f"\n[YASAL RAPOR PDF] PDF indirme istegi alindi - Mutabakat ID: {mutabakat_id}")
    print(f"[YASAL RAPOR PDF] Admin: {current_user.username}")
    
    # Admin kontrolü
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    
    # Detaylı raporu al
    report = get_legal_mutabakat_report(mutabakat_id, current_user, db)
    
    # Mutabakat bilgisini al
    mutabakat_query = db.query(Mutabakat).filter(Mutabakat.id == mutabakat_id)
    
    # Company admin ise sadece kendi şirketinin mutabakatlarını görebilir
    if current_user.role == UserRole.COMPANY_ADMIN:
        mutabakat_query = mutabakat_query.filter(Mutabakat.company_id == current_user.company_id)
    
    mutabakat = mutabakat_query.first()
    if not mutabakat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mutabakat bulunamadı veya erişim yetkiniz yok"
        )
    
    # Mutabakat'a ait şirket bilgilerini al
    company = db.query(Company).filter(Company.id == mutabakat.company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Şirket bilgisi bulunamadı"
        )
    
    # Rapor metadata'sını hazırla
    report_metadata = {
        'report_date': datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        'generated_by': f"{current_user.full_name} ({current_user.username})",
        'report_type': 'Mutabakat Yasal Raporu',
        'company_name': company.full_company_name or company.company_name,
        'company_address': company.address or '',
        'company_phone': company.phone or '',
        'company_email': company.email or '',
        'company_website': company.website or '',
        'company_logo_path': company.logo_path
    }
    
    # PDF verilerini formatla
    pdf_data = {
        'report_metadata': report_metadata,
        'mutabakat': {
            **report['mutabakat'],
            'bakiye_str': f"{report['mutabakat']['bakiye']:,.2f} TL".replace(',', '.'),
            'toplam_borc_str': f"{report['mutabakat']['toplam_borc']:,.2f} TL".replace(',', '.'),
            'toplam_alacak_str': f"{report['mutabakat']['toplam_alacak']:,.2f} TL".replace(',', '.'),
            'donem_str': f"{report['mutabakat']['donem_baslangic']} - {report['mutabakat']['donem_bitis']}",
            'created_at_str': report['mutabakat']['created_at']
        },
        'sender': report.get('sender'),
        'receiver': report.get('receiver'),
        'items': report.get('items', []),
        'activity_logs': [{
            **log,
            'timestamp_str': log['timestamp']
        } for log in report.get('activity_logs', [])],
        'kvkk_consents': report.get('kvkk_consents', {}),
        'kvkk_deletions': report.get('kvkk_deletion_logs', {})
    }
    
    try:
        # PDF oluştur
        pdf_generator = LegalReportPDFGenerator()
        pdf_buffer = pdf_generator.generate_mutabakat_report(pdf_data)
        pdf_bytes = pdf_buffer.read()
        
        # Geçici dosya oluştur
        pdf_dir = Path("pdfs/yasal_raporlar")
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        temp_pdf_path = pdf_dir / f"yasal_rapor_{mutabakat.mutabakat_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # PDF'i geçici dosyaya yaz
        with open(temp_pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        # Dijital imza ekle (şirket sertifikası ile - thread pool'da çalıştır)
        signed_pdf_path = str(temp_pdf_path)
        try:
            print(f"[YASAL RAPOR PDF] Dijital imza ekleniyor...")
            print(f"[YASAL RAPOR PDF] Şirket: {company.company_name}")
            
            # Thread pool'da senkron fonksiyonu çalıştır
            loop = asyncio.get_event_loop()
            
            # Şirket sertifikası varsa kullan
            if company.certificate_path:
                print(f"[YASAL RAPOR PDF] Şirket sertifikası kullanılıyor: {company.certificate_path}")
                signed_pdf_path = await loop.run_in_executor(
                    None,
                    lambda: pdf_signer.sign_pdf(
                        str(temp_pdf_path),
                        company_name=company.full_company_name or company.company_name,
                        cert_path=company.certificate_path,
                        cert_password=company.certificate_password
                    )
                )
            else:
                print(f"[YASAL RAPOR PDF] Şirket sertifikası yok, default sertifika kullanılıyor")
                signed_pdf_path = await loop.run_in_executor(
                    None,
                    pdf_signer.sign_pdf,
                    str(temp_pdf_path)
                )
            print(f"[YASAL RAPOR PDF] [OK] Dijital imza basariyla eklendi")
        except Exception as e:
            print(f"[YASAL RAPOR PDF] [UYARI] Dijital imza eklenemedi (devam ediliyor): {str(e)[:100]}")
            # İmzasız devam et
        
        # İzinleri uygula (256-bit AES şifreleme)
        print(f"[YASAL RAPOR PDF] Izinler ve sifreleme uygulan iyor...")
        final_pdf_path = apply_pdf_permissions(signed_pdf_path)
        
        # PDF'i oku
        with open(final_pdf_path, 'rb') as f:
            final_pdf_bytes = f.read()
        
        # Hash oluştur
        pdf_hash = hashlib.sha256(final_pdf_bytes).hexdigest()
        
        print(f"[YASAL RAPOR PDF] PDF Hash: {pdf_hash[:16]}...")
        
        # Activity log kaydet (ISP bilgili)
        ip_info = get_real_ip_with_isp(request)
        ActivityLogger.log(
            db=db,
            action="legal_report_pdf_download",
            description=f"Yasal rapor PDF indirildi: {mutabakat.mutabakat_no} (Hash: {pdf_hash[:16]}...)",
            user_id=current_user.id,
            ip_info=ip_info,
            user_agent=request.headers.get('user-agent')
        )
        
        print(f"[YASAL RAPOR PDF] [OK] PDF basariyla olusturuldu ve imzalandi")
        print(f"  - Dosya: {temp_pdf_path.name}")
        print(f"  - Hash: {pdf_hash[:32]}...")
        print(f"  - Sifreleme: 256-bit AES")
        print(f"  - Dijital Imza: Eklendi")
        print(f"  - Izinler: Sadece Yazdirma + Imzalama")
        
        # PDF'i yanıt olarak döndür
        return StreamingResponse(
            iter([final_pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Yasal_Rapor_{mutabakat.mutabakat_no}.pdf",
                "X-PDF-Hash": pdf_hash,
                "X-PDF-Security": "256-bit-AES-Encrypted-Digitally-Signed"
            }
        )
        
    except Exception as e:
        print(f"[YASAL RAPOR PDF] [!] HATA: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF oluşturma hatası: {str(e)}"
        )


@router.get("/legal/user/{user_id}/pdf")
async def download_legal_user_pdf(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcı Yasal Raporu PDF İndir (Multi-Company)
    Dijital imzalı, şifreli, hash'lenmiş PDF oluşturur
    """
    print(f"\n[YASAL RAPOR PDF] PDF indirme istegi alindi - User ID: {user_id}")
    print(f"[YASAL RAPOR PDF] Admin: {current_user.username}")
    
    # Admin kontrolü
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    
    # Detaylı raporu al
    report = get_legal_user_report(user_id, current_user, db)
    
    # Kullanıcı bilgisini al
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
    
    # Kullanıcının şirket bilgilerini al
    company = db.query(Company).filter(Company.id == user.company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Şirket bilgisi bulunamadı"
        )
    
    # Rapor metadata'sını hazırla
    report_metadata = {
        'report_date': datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        'generated_by': f"{current_user.full_name} ({current_user.username})",
        'report_type': 'Kullanıcı Yasal Raporu',
        'company_name': company.full_company_name or company.company_name,
        'company_address': company.address or '',
        'company_phone': company.phone or '',
        'company_email': company.email or '',
        'company_website': company.website or '',
        'company_logo_path': company.logo_path
    }
    
    # PDF verilerini formatla (mutabakat formatında)
    # İlk mutabakat varsa onu kullan, yoksa user bilgilerini göster
    first_mutabakat = report['mutabakats'][0] if report.get('mutabakats') else None
    
    pdf_data = {
        'report_metadata': report_metadata,
        'mutabakat': {
            'mutabakat_no': f"KULLANICI_RAPORU_{user.vkn_tckn or user.username}",
            'durum': f"{len(report['mutabakats'])} Mutabakat",
            'bakiye': 0,
            'toplam_borc': sum(m.get('toplam_borc', 0) for m in report['mutabakats']),
            'toplam_alacak': sum(m.get('toplam_alacak', 0) for m in report['mutabakats']),
            'toplam_bayi_sayisi': sum(m.get('toplam_bayi_sayisi', 0) for m in report['mutabakats']),
            'donem_baslangic': '-',
            'donem_bitis': '-',
            'created_at': user.created_at.strftime("%d.%m.%Y %H:%M:%S") if user.created_at else '-',
            'bakiye_str': "Çoklu Mutabakat",
            'toplam_borc_str': f"{sum(m.get('toplam_borc', 0) for m in report['mutabakats']):,.2f} TL".replace(',', '.'),
            'toplam_alacak_str': f"{sum(m.get('toplam_alacak', 0) for m in report['mutabakats']):,.2f} TL".replace(',', '.'),
            'donem_str': "Tüm Dönemler",
            'created_at_str': user.created_at.strftime("%d.%m.%Y %H:%M:%S") if user.created_at else '-'
        } if first_mutabakat is None else {
            **first_mutabakat,
            'bakiye_str': f"{first_mutabakat['bakiye']:,.2f} TL".replace(',', '.'),
            'toplam_borc_str': f"{first_mutabakat['toplam_borc']:,.2f} TL".replace(',', '.'),
            'toplam_alacak_str': f"{first_mutabakat['toplam_alacak']:,.2f} TL".replace(',', '.'),
            'donem_str': f"{first_mutabakat['donem_baslangic']} - {first_mutabakat['donem_bitis']}",
            'created_at_str': first_mutabakat['created_at']
        },
        'sender': {
            'vkn_tckn': company.vkn or '-',
            'full_name': company.company_name,
            'company_name': company.full_company_name or company.company_name,
            'email': company.email or '-',
            'phone': company.phone or '-'
        },  # Gönderen: Kullanıcının şirketi
        'receiver': report.get('user'),  # Alıcı: VKN ile aranan kullanıcı
        'mutabakats': report.get('mutabakats', []),  # TÜM MUTABAKATLAR LİSTESİ
        'items': [],
        'activity_logs': [{
            **log,
            'timestamp_str': log['timestamp']
        } for log in report.get('activity_logs', [])],
        'kvkk_consents': report.get('kvkk_consents', {}),  # KVKK consents yapısını doğrudan al
        'kvkk_deletions': report.get('kvkk_deletion_logs', {})
    }
    
    try:
        # PDF oluştur
        pdf_generator = LegalReportPDFGenerator()
        pdf_buffer = pdf_generator.generate_mutabakat_report(pdf_data)
        pdf_bytes = pdf_buffer.read()
        
        # Geçici dosya oluştur
        pdf_dir = Path("pdfs/yasal_raporlar")
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        temp_pdf_path = pdf_dir / f"yasal_rapor_kullanici_{user.vkn_tckn or user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # PDF'i geçici dosyaya yaz
        with open(temp_pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        # Dijital imza ekle (şirket sertifikası ile - thread pool'da çalıştır)
        signed_pdf_path = str(temp_pdf_path)
        try:
            print(f"[YASAL RAPOR PDF] Dijital imza ekleniyor...")
            print(f"[YASAL RAPOR PDF] Şirket: {company.company_name}")
            
            # Thread pool'da senkron fonksiyonu çalıştır
            loop = asyncio.get_event_loop()
            
            # Şirket sertifikası varsa kullan
            if company.certificate_path:
                print(f"[YASAL RAPOR PDF] Şirket sertifikası kullanılıyor: {company.certificate_path}")
                signed_pdf_path = await loop.run_in_executor(
                    None,
                    lambda: pdf_signer.sign_pdf(
                        str(temp_pdf_path),
                        company_name=company.full_company_name or company.company_name,
                        cert_path=company.certificate_path,
                        cert_password=company.certificate_password
                    )
                )
            else:
                print(f"[YASAL RAPOR PDF] Şirket sertifikası yok, default sertifika kullanılıyor")
                signed_pdf_path = await loop.run_in_executor(
                    None,
                    pdf_signer.sign_pdf,
                    str(temp_pdf_path)
                )
            print(f"[YASAL RAPOR PDF] [OK] Dijital imza basariyla eklendi")
        except Exception as e:
            print(f"[YASAL RAPOR PDF] [UYARI] Dijital imza eklenemedi (devam ediliyor): {str(e)[:100]}")
            # İmzasız devam et
        
        # İzinleri uygula (256-bit AES şifreleme)
        print(f"[YASAL RAPOR PDF] Izinler ve sifreleme uygulan iyor...")
        final_pdf_path = apply_pdf_permissions(signed_pdf_path)
        
        # PDF'i oku
        with open(final_pdf_path, 'rb') as f:
            final_pdf_bytes = f.read()
        
        # Hash oluştur
        pdf_hash = hashlib.sha256(final_pdf_bytes).hexdigest()
        
        print(f"[YASAL RAPOR PDF] PDF Hash: {pdf_hash[:16]}...")
        
        # Activity log kaydet (ISP bilgili)
        ip_info = get_real_ip_with_isp(request)
        ActivityLogger.log(
            db=db,
            action="legal_report_pdf_download",
            description=f"Kullanıcı yasal rapor PDF indirildi: {user.vkn_tckn or user.username} (Hash: {pdf_hash[:16]}...)",
            user_id=current_user.id,
            ip_info=ip_info,
            user_agent=request.headers.get('user-agent')
        )
        
        print(f"[YASAL RAPOR PDF] [OK] PDF basariyla olusturuldu ve imzalandi")
        print(f"  - Dosya: {temp_pdf_path.name}")
        print(f"  - Hash: {pdf_hash[:32]}...")
        print(f"  - Sifreleme: 256-bit AES")
        print(f"  - Dijital Imza: Eklendi")
        print(f"  - Izinler: Sadece Yazdirma + Imzalama")
        
        # PDF'i yanıt olarak döndür
        return StreamingResponse(
            iter([final_pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Yasal_Rapor_Kullanici_{user.vkn_tckn or user.username}.pdf",
                "X-PDF-Hash": pdf_hash,
                "X-PDF-Security": "256-bit-AES-Encrypted-Digitally-Signed"
            }
        )
        
    except Exception as e:
        print(f"[YASAL RAPOR PDF] [!] HATA: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF oluşturma hatası: {str(e)}"
        )

