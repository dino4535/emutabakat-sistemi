from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from backend.database import get_db
from backend.models import User, Mutabakat, MutabakatItem, MutabakatDurumu, UserRole, Bayi, MutabakatBayiDetay, Company
from backend.schemas import (
    MutabakatCreate,
    MutabakatResponse,
    MutabakatDetailResponse,
    MutabakatUpdate
)
from backend.auth import get_current_active_user
from backend.logger import ActivityLogger
from backend.middleware.rate_limiter import RateLimiter, RateLimitRules
from backend.sms import sms_service
from backend.utils.pdf_service import create_mutabakat_pdf
from backend.utils.pdf_signer import pdf_signer
from backend.utils.pdf_permissions import apply_pdf_permissions
from backend.utils.pagination import Paginator, SortableColumns
from backend.utils.cache_manager import cache_manager
import random
import string
import os
import requests
from datetime import datetime, timedelta
import pytz

# Türkiye saat dilimi
TURKEY_TZ = pytz.timezone('Europe/Istanbul')

def get_turkey_time():
    """Türkiye saatini döndür (UTC+3)"""
    return datetime.now(TURKEY_TZ)

def invalidate_mutabakat_caches(sender_id: int = None, receiver_id: int = None):
    """Mutabakat işlemlerinde cache'leri temizle"""
    if sender_id:
        cache_manager.delete(f"cache:dashboard_stats:{sender_id}")
    if receiver_id:
        cache_manager.delete(f"cache:dashboard_stats:{receiver_id}")

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
                    print(f"[IP] Şehir: {ip_info['city']}, {ip_info['region']}")
                    print(f"[IP] Ülke: {ip_info['country']}")
                    print(f"[IP] Organizasyon: {ip_info['org']}")
        except Exception as e:
            print(f"[IP] ISP bilgisi alınamadı: {e}")
    
    return ip_info

def get_real_ip(request: Request) -> str:
    """Eski fonksiyon - geriye dönük uyumluluk için"""
    return get_real_ip_with_isp(request)["ip"]

router = APIRouter(prefix="/api/mutabakat", tags=["Mutabakat"])

# Pydantic Models
class ManualMutabakatCreateRequest(BaseModel):
    receiver_vkn: str
    donem_baslangic: str
    donem_bitis: str
    toplam_borc: float
    toplam_alacak: float
    aciklama: Optional[str] = None
    bayiler: Optional[List[dict]] = []

def generate_mutabakat_no() -> str:
    """Benzersiz mutabakat numarası oluştur"""
    timestamp = get_turkey_time().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"MUT-{timestamp}-{random_str}"

@router.post("/", response_model=MutabakatResponse, status_code=status.HTTP_201_CREATED)
@RateLimiter.limit(**RateLimitRules.MUTABAKAT_CREATE)
async def create_mutabakat(
    mutabakat: MutabakatCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Yeni mutabakat belgesi oluştur (Multi-Company)"""
    
    # Alıcı kontrolü
    # Sistem admini (ADMIN) tüm şirketlerin müşterilerine mutabakat gönderebilir
    # Diğer kullanıcılar (COMPANY_ADMIN, MUHASEBE, PLANLAMA) sadece kendi şirketlerine
    receiver_query = db.query(User).filter(User.id == mutabakat.receiver_id)
    
    if current_user.role != UserRole.ADMIN:
        # Sistem admini değilse, sadece kendi şirketinden alıcıya gönderebilir
        receiver_query = receiver_query.filter(User.company_id == current_user.company_id)
    
    receiver = receiver_query.first()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alıcı bulunamadı veya erişim yetkiniz yok"
        )
    
    if receiver.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kendinize mutabakat gönderemezsiniz"
        )
    
    # Mutabakat oluştur (Bakiye Mutabakatı - Kalemsiz)
    # ÖNEMLI: Mutabakat, ALICININ ŞİRKETİNE ait olmalı (Multi-Company)
    db_mutabakat = Mutabakat(
        company_id=receiver.company_id,  # Alıcının şirket ID'si (düzeltildi)
        mutabakat_no=generate_mutabakat_no(),
        sender_id=current_user.id,
        receiver_id=mutabakat.receiver_id,
        receiver_vkn=receiver.vkn_tckn,  # VKN'yi de kaydet
        donem_baslangic=mutabakat.donem_baslangic,
        donem_bitis=mutabakat.donem_bitis,
        toplam_borc=mutabakat.toplam_borc,
        toplam_alacak=mutabakat.toplam_alacak,
        bakiye=mutabakat.toplam_alacak - mutabakat.toplam_borc,
        aciklama=mutabakat.aciklama,
        durum=MutabakatDurumu.TASLAK
    )
    
    db.add(db_mutabakat)
    db.commit()
    db.refresh(db_mutabakat)
    
    # Log kaydet (ISP bilgili - Yasal Delil için)
    ip_info = get_real_ip_with_isp(request)
    ActivityLogger.log_mutabakat_created(
        db,
        current_user.id,
        db_mutabakat.mutabakat_no,
        ip_info
    )
    
    return db_mutabakat

@router.get("/")
def get_mutabakats(
    page: int = 1,
    page_size: int = 50,
    order_by: str = "created_at",
    order_direction: str = "desc",
    search: str = None,
    durum: MutabakatDurumu = None,
    sender_id: int = None,
    receiver_id: int = None,
    date_start: str = None,
    date_end: str = None,
    amount_min: float = None,
    amount_max: float = None,
    company: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Mutabakatları listele (Multi-Company & Role-Based) - Pagination & Sorting ile
    
    Query Parameters:
        - page: Sayfa numarası (default: 1)
        - page_size: Sayfa başına kayıt (default: 50, max: 200)
        - order_by: Sıralama kolonu (default: created_at)
        - order_direction: Sıralama yönü (asc/desc, default: desc)
        - search: Arama (mutabakat_no, receiver_vkn)
        - durum: Durum filtresi
        - sender_id: Gönderen ID filtresi
        - receiver_id: Alıcı ID filtresi
        - date_start: Başlangıç tarihi (YYYY-MM-DD)
        - date_end: Bitiş tarihi (YYYY-MM-DD)
        - amount_min: Minimum tutar
        - amount_max: Maximum tutar
        - company: Şirket adı (partial match)
    """
    from sqlalchemy.orm import joinedload
    
    # Sorgu oluştur
    query = db.query(Mutabakat).options(
        joinedload(Mutabakat.sender),
        joinedload(Mutabakat.receiver)
    )
    
    # Role-based filtering
    if current_user.role == UserRole.ADMIN:
        # Sistem admini: TÜM mutabakatları görebilir
        pass  # Filtre yok
    elif current_user.role in [UserRole.COMPANY_ADMIN, UserRole.MUHASEBE, UserRole.PLANLAMA]:
        # Şirket admini, Muhasebe, Planlama: Kendi şirketinin TÜM mutabakatlarını görebilir
        query = query.filter(Mutabakat.company_id == current_user.company_id)
    else:
        # Müşteri/Tedarikçi: Sadece gönderilen veya alınan mutabakatlar
        query = query.filter(
            and_(
                Mutabakat.company_id == current_user.company_id,
                or_(
                    Mutabakat.sender_id == current_user.id,
                    Mutabakat.receiver_id == current_user.id
                )
            )
        )
    
    # Arama filtresi
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Mutabakat.mutabakat_no.ilike(search_pattern),
                Mutabakat.receiver_vkn.ilike(search_pattern)
            )
        )
    
    # Durum filtresi
    if durum:
        query = query.filter(Mutabakat.durum == durum)
    
    # Sender filtresi
    if sender_id:
        query = query.filter(Mutabakat.sender_id == sender_id)
    
    # Receiver filtresi
    if receiver_id:
        query = query.filter(Mutabakat.receiver_id == receiver_id)
    
    # Tarih aralığı filtresi (created_at bazlı)
    if date_start:
        try:
            start_date = datetime.strptime(date_start, "%Y-%m-%d")
            query = query.filter(Mutabakat.created_at >= start_date)
        except ValueError:
            pass  # Geçersiz tarih formatı, filtre skip
    
    if date_end:
        try:
            end_date = datetime.strptime(date_end, "%Y-%m-%d")
            # Gün sonuna kadar dahil et
            end_date = end_date.replace(hour=23, minute=59, second=59)
            query = query.filter(Mutabakat.created_at <= end_date)
        except ValueError:
            pass  # Geçersiz tarih formatı, filtre skip
    
    # Tutar aralığı filtresi (bakiye bazlı)
    if amount_min is not None:
        query = query.filter(Mutabakat.bakiye >= amount_min)
    
    if amount_max is not None:
        query = query.filter(Mutabakat.bakiye <= amount_max)
    
    # Şirket adı filtresi (sender veya receiver bazlı)
    if company:
        company_pattern = f"%{company}%"
        query = query.join(User, or_(
            Mutabakat.sender_id == User.id,
            Mutabakat.receiver_id == User.id
        )).filter(
            or_(
                User.company_name.ilike(company_pattern),
                User.full_name.ilike(company_pattern)
            )
        )
    
    # Güvenli sıralama kolonu
    safe_order_by = SortableColumns.get_safe_column(order_by, SortableColumns.MUTABAKAT)
    
    # Paginate
    result = Paginator.paginate(
        query=query,
        page=page,
        page_size=page_size,
        order_by=safe_order_by,
        order_direction=order_direction,
        model_class=Mutabakat
    )
    
    mutabakats = result["items"]
    
    # Manuel serialize et
    serialized_items = []
    for m in mutabakats:
        mutabakat_dict = {
            "id": m.id,
            "mutabakat_no": m.mutabakat_no,
            "sender_id": m.sender_id,
            "receiver_id": m.receiver_id,
            "donem_baslangic": m.donem_baslangic,
            "donem_bitis": m.donem_bitis,
            "toplam_borc": m.toplam_borc,
            "toplam_alacak": m.toplam_alacak,
            "bakiye": m.bakiye,
            "durum": m.durum,
            "aciklama": m.aciklama,
            "red_nedeni": m.red_nedeni,
            "gonderim_tarihi": m.gonderim_tarihi,
            "onay_tarihi": m.onay_tarihi,
            "red_tarihi": m.red_tarihi,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
            "items": [],
            "sender": {
                "id": m.sender.id,
                "username": m.sender.username,
                "full_name": m.sender.full_name,
                "company_name": m.sender.company_name
            } if m.sender else None,
            "receiver": {
                "id": m.receiver.id,
                "username": m.receiver.username,
                "full_name": m.receiver.full_name,
                "company_name": m.receiver.company_name
            } if m.receiver else None
        }
        serialized_items.append(mutabakat_dict)
    
    return {
        "items": serialized_items,
        "metadata": result["metadata"]
    }

@router.get("/{mutabakat_id}", response_model=MutabakatDetailResponse)
def get_mutabakat(
    mutabakat_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mutabakat detayını getir (Multi-Company & Role-Based)"""
    
    # Sorgu oluştur
    query = db.query(Mutabakat).filter(Mutabakat.id == mutabakat_id)
    
    # Role-based filtering
    if current_user.role == UserRole.ADMIN:
        # Sistem admini: TÜM mutabakatları görebilir
        pass  # Filtre yok
    elif current_user.role in [UserRole.COMPANY_ADMIN, UserRole.MUHASEBE, UserRole.PLANLAMA]:
        # Şirket admini, Muhasebe, Planlama: Kendi şirketinin TÜM mutabakatlarını görebilir
        query = query.filter(Mutabakat.company_id == current_user.company_id)
    else:
        # Müşteri/Tedarikçi: Sadece gönderilen veya alınan mutabakatlar
        query = query.filter(
            and_(
                Mutabakat.company_id == current_user.company_id,
                or_(
                    Mutabakat.sender_id == current_user.id,
                    Mutabakat.receiver_id == current_user.id
                )
            )
        )
    
    mutabakat = query.first()
    
    if not mutabakat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mutabakat bulunamadı veya erişim yetkiniz yok"
        )
    
    return mutabakat

@router.put("/{mutabakat_id}", response_model=MutabakatResponse)
def update_mutabakat(
    mutabakat_id: int,
    mutabakat_update: MutabakatUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mutabakat güncelle (sadece taslak olanlar)"""
    
    mutabakat = db.query(Mutabakat).filter(Mutabakat.id == mutabakat_id).first()
    
    if not mutabakat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mutabakat bulunamadı"
        )
    
    # Sadece gönderen güncelleyebilir
    if mutabakat.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu mutabakatı güncelleme yetkiniz yok"
        )
    
    # Sadece taslak olanlar güncellenebilir
    if mutabakat.durum != MutabakatDurumu.TASLAK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece taslak mutabakatlar güncellenebilir"
        )
    
    # Güncelle
    for field, value in mutabakat_update.model_dump(exclude_unset=True).items():
        setattr(mutabakat, field, value)
    
    db.commit()
    db.refresh(mutabakat)
    
    return mutabakat

@router.post("/{mutabakat_id}/send")
def send_mutabakat(
    mutabakat_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mutabakatı gönder (Role-Based Access)"""
    
    mutabakat = db.query(Mutabakat).filter(Mutabakat.id == mutabakat_id).first()
    
    if not mutabakat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mutabakat bulunamadı"
        )
    
    # Yetki kontrolü (Role-Based)
    can_send = False
    
    if current_user.role == UserRole.ADMIN:
        # Sistem admini tüm mutabakatları gönderebilir
        can_send = True
    elif current_user.role in [UserRole.COMPANY_ADMIN, UserRole.MUHASEBE, UserRole.PLANLAMA]:
        # Şirket admini, Muhasebe, Planlama: Kendi şirketinin mutabakatlarını gönderebilir
        can_send = (mutabakat.company_id == current_user.company_id)
    else:
        # Müşteri/Tedarikçi: Sadece kendi oluşturduğu mutabakatları gönderebilir
        can_send = (mutabakat.sender_id == current_user.id)
    
    if not can_send:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu mutabakatı gönderme yetkiniz yok"
        )
    
    if mutabakat.durum != MutabakatDurumu.TASLAK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece taslak mutabakatlar gönderilebilir"
        )
    
    # Durumu güncelle
    mutabakat.durum = MutabakatDurumu.GONDERILDI
    mutabakat.gonderim_tarihi = datetime.utcnow()
    
    # Tek kullanımlık onay token'ı oluştur
    from backend.utils.tokens import create_approval_token
    approval_token = create_approval_token(db, mutabakat.id)
    
    db.commit()
    db.refresh(mutabakat)
    
    # Log kaydet (ISP bilgili - Yasal Delil için)
    ip_info = get_real_ip_with_isp(request)
    ActivityLogger.log_mutabakat_sent(
        db,
        current_user.id,
        mutabakat.mutabakat_no,
        ip_info
    )
    
    # SMS gönder (alıcıya) - Onay linki ile
    sms_info = "SMS gönderilemedi"
    receiver = db.query(User).filter(User.id == mutabakat.receiver_id).first()
    if receiver and receiver.phone:
        try:
            receiver_name = receiver.company_name or receiver.full_name or receiver.username
            sms_service.send_mutabakat_notification(
                phone=receiver.phone,
                customer_name=receiver_name,
                mutabakat_no=mutabakat.mutabakat_no,
                amount=abs(mutabakat.bakiye),
                approval_token=approval_token  # Token'ı SMS'e ekle
            )
            sms_info = f"SMS başarıyla gönderildi: {receiver.phone}"
        except Exception as e:
            # SMS hatası logla ama işlemi durma
            sms_info = f"SMS gönderilemedi: {str(e)}"
            ActivityLogger.log_error(
                db,
                f"SMS gönderme hatası: {e}",
                current_user.id,
                request.client.host if request.client else "unknown"
            )
    else:
        sms_info = "Alıcının telefon numarası bulunamadı"
    
    # Custom response: hem mutabakat hem de SMS bilgisi
    return {
        "mutabakat": mutabakat,
        "message": sms_info,
        "success": True
    }

@router.post("/send-all-drafts")
def send_all_draft_mutabakats(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Tüm taslak mutabakatları toplu gönder (Role-Based Access)"""
    
    # Taslak mutabakatları filtrele
    query = db.query(Mutabakat).filter(Mutabakat.durum == MutabakatDurumu.TASLAK)
    
    # Role-based filtering
    if current_user.role == UserRole.ADMIN:
        # Sistem admini: TÜM taslak mutabakatları gönderebilir
        pass  # Filtre yok
    elif current_user.role in [UserRole.COMPANY_ADMIN, UserRole.MUHASEBE, UserRole.PLANLAMA]:
        # Şirket admini, Muhasebe, Planlama: Kendi şirketinin taslak mutabakatlarını gönderebilir
        query = query.filter(Mutabakat.company_id == current_user.company_id)
    else:
        # Müşteri/Tedarikçi: Sadece kendi oluşturduğu taslak mutabakatları gönderebilir
        query = query.filter(Mutabakat.sender_id == current_user.id)
    
    draft_mutabakats = query.all()
    
    if not draft_mutabakats:
        return {
            "success": True,
            "message": "Gönderilecek taslak mutabakat bulunamadı",
            "sent_count": 0,
            "failed_count": 0,
            "details": []
        }
    
    # IP bilgisini al (loglar için)
    ip_info = get_real_ip_with_isp(request)
    
    sent_count = 0
    failed_count = 0
    details = []
    
    for mutabakat in draft_mutabakats:
        try:
            # Durumu güncelle
            mutabakat.durum = MutabakatDurumu.GONDERILDI
            mutabakat.gonderim_tarihi = datetime.utcnow()
            
            # Tek kullanımlık onay token'ı oluştur
            from backend.utils.tokens import create_approval_token
            approval_token = create_approval_token(db, mutabakat.id)
            
            # Log kaydet
            ActivityLogger.log_mutabakat_sent(
                db,
                current_user.id,
                mutabakat.mutabakat_no,
                ip_info
            )
            
            # SMS gönder (alıcıya)
            sms_sent = False
            receiver = db.query(User).filter(User.id == mutabakat.receiver_id).first()
            if receiver and receiver.phone:
                try:
                    receiver_name = receiver.company_name or receiver.full_name or receiver.username
                    sms_service.send_mutabakat_notification(
                        phone=receiver.phone,
                        customer_name=receiver_name,
                        mutabakat_no=mutabakat.mutabakat_no,
                        amount=abs(mutabakat.bakiye),
                        approval_token=approval_token
                    )
                    sms_sent = True
                except Exception as e:
                    print(f"[TOPLU GONDERIM] SMS hatasi: {e}")
            
            sent_count += 1
            details.append({
                "mutabakat_no": mutabakat.mutabakat_no,
                "receiver": receiver.company_name if receiver else "Bilinmiyor",
                "sms_sent": sms_sent,
                "status": "success"
            })
            
        except Exception as e:
            failed_count += 1
            details.append({
                "mutabakat_no": mutabakat.mutabakat_no,
                "status": "failed",
                "error": str(e)
            })
    
    # Değişiklikleri kaydet
    db.commit()
    
    return {
        "success": True,
        "message": f"{sent_count} mutabakat başarıyla gönderildi" + (f", {failed_count} hata" if failed_count > 0 else ""),
        "sent_count": sent_count,
        "failed_count": failed_count,
        "details": details
    }

@router.post("/{mutabakat_id}/approve", response_model=MutabakatResponse)
def approve_mutabakat(
    mutabakat_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mutabakatı onayla"""
    
    mutabakat = db.query(Mutabakat).filter(Mutabakat.id == mutabakat_id).first()
    
    if not mutabakat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mutabakat bulunamadı"
        )
    
    if mutabakat.receiver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu mutabakatı onaylama yetkiniz yok"
        )
    
    if mutabakat.durum != MutabakatDurumu.GONDERILDI:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece gönderilmiş mutabakatlar onaylanabilir"
        )
    
    # Durumu güncelle
    mutabakat.durum = MutabakatDurumu.ONAYLANDI
    mutabakat.onay_tarihi = datetime.utcnow()
    
    # PDF lazy generation: istendiğinde oluşturulacak (hız için)
    
    db.commit()
    db.refresh(mutabakat)
    
    # Log kaydet (ISP bilgili - Yasal Delil için)
    ip_info = get_real_ip_with_isp(request)
    ActivityLogger.log_mutabakat_approved(
        db,
        current_user.id,
        mutabakat.mutabakat_no,
        ip_info
    )
    
    # Email gönder (gönderene - şirketin notification email'ine)
    sender = db.query(User).filter(User.id == mutabakat.sender_id).first()
    sender_company = db.query(Company).filter(Company.id == sender.company_id).first() if sender else None
    
    if sender_company and sender_company.notification_email:
        try:
            from backend.utils.email_service import email_service
            
            customer_name = current_user.company_name or current_user.full_name or current_user.username
            email_service.send_mutabakat_approved(
                to_email=sender_company.notification_email,
                company_name=sender_company.company_name,
                customer_name=customer_name,
                mutabakat_no=mutabakat.mutabakat_no,
                donem_baslangic=mutabakat.donem_baslangic,
                donem_bitis=mutabakat.donem_bitis,
                toplam_borc=mutabakat.toplam_borc,
                toplam_alacak=mutabakat.toplam_alacak,
                bakiye=mutabakat.bakiye,
                onay_tarihi=mutabakat.onay_tarihi
            )
        except Exception as e:
            # Email hatası logla ama işlemi durma
            ActivityLogger.log_error(
                db,
                f"Email gönderme hatası: {e}",
                current_user.id,
                request.client.host if request.client else "unknown"
            )
    
    return mutabakat

@router.post("/{mutabakat_id}/reject", response_model=MutabakatResponse)
def reject_mutabakat(
    mutabakat_id: int,
    red_nedeni: str,
    ekstre_talep_edildi: bool = False,
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mutabakatı reddet ve opsiyonel olarak detaylı ekstre talep et"""
    
    mutabakat = db.query(Mutabakat).filter(Mutabakat.id == mutabakat_id).first()
    
    if not mutabakat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mutabakat bulunamadı"
        )
    
    if mutabakat.receiver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu mutabakatı reddetme yetkiniz yok"
        )
    
    if mutabakat.durum != MutabakatDurumu.GONDERILDI:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece gönderilmiş mutabakatlar reddedilebilir"
        )
    
    # Durumu güncelle
    mutabakat.durum = MutabakatDurumu.REDDEDILDI
    mutabakat.red_tarihi = datetime.utcnow()
    mutabakat.red_nedeni = red_nedeni
    mutabakat.ekstre_talep_edildi = ekstre_talep_edildi
    
    # PDF lazy generation: istendiğinde oluşturulacak (hız için)
    
    db.commit()
    db.refresh(mutabakat)
    
    # Log kaydet (ISP bilgili - Yasal Delil için)
    ip_info = get_real_ip_with_isp(request)
    ActivityLogger.log_mutabakat_rejected(
        db,
        current_user.id,
        mutabakat.mutabakat_no,
        red_nedeni,
        ip_info
    )
    
    # Email gönder (gönderene - şirketin notification email'ine)
    sender = db.query(User).filter(User.id == mutabakat.sender_id).first()
    sender_company = db.query(Company).filter(Company.id == sender.company_id).first() if sender else None
    
    if sender_company and sender_company.notification_email:
        try:
            from backend.utils.email_service import email_service
            
            customer_name = current_user.company_name or current_user.full_name or current_user.username
            email_service.send_mutabakat_rejected(
                to_email=sender_company.notification_email,
                company_name=sender_company.company_name,
                customer_name=customer_name,
                mutabakat_no=mutabakat.mutabakat_no,
                donem_baslangic=mutabakat.donem_baslangic,
                donem_bitis=mutabakat.donem_bitis,
                toplam_borc=mutabakat.toplam_borc,
                toplam_alacak=mutabakat.toplam_alacak,
                bakiye=mutabakat.bakiye,
                red_nedeni=red_nedeni,
                red_tarihi=mutabakat.red_tarihi
            )
        except Exception as e:
            # Email hatası logla ama işlemi durma
            ActivityLogger.log_error(
                db,
                f"Email gönderme hatası: {e}",
                current_user.id,
                request.client.host if request.client else "unknown"
            )
    
    return mutabakat

@router.get("/{mutabakat_id}/download-pdf")
@RateLimiter.limit(**RateLimitRules.PDF_DOWNLOAD)
async def download_mutabakat_pdf(
    mutabakat_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mutabakat PDF'ini indir (lazy generation - istendiğinde oluştur)"""
    
    mutabakat = db.query(Mutabakat).filter(Mutabakat.id == mutabakat_id).first()
    
    if not mutabakat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mutabakat bulunamadı"
        )
    
    # Yetki kontrolü: Admin, Company Admin veya gönderen/alıcı olmalı
    is_admin = current_user.role == 'admin'
    is_company_admin_of_mutabakat = (
        current_user.role == 'company_admin' and 
        current_user.company_id == mutabakat.company_id
    )
    is_sender_or_receiver = (
        mutabakat.sender_id == current_user.id or 
        mutabakat.receiver_id == current_user.id
    )
    
    if not (is_admin or is_company_admin_of_mutabakat or is_sender_or_receiver):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu mutabakatın PDF'ine erişim yetkiniz yok"
        )
    
    # Mutabakat onaylı veya reddedilmiş olmalı
    if mutabakat.durum not in [MutabakatDurumu.ONAYLANDI, MutabakatDurumu.REDDEDILDI]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF belgesi sadece onaylanan veya reddedilen mutabakatlar için oluşturulabilir."
        )
    
    # PDF dosyası yoksa veya silinmişse, şimdi oluştur (LAZY GENERATION)
    if not mutabakat.pdf_file_path or not os.path.exists(mutabakat.pdf_file_path):
        try:
            # Gerçek public IP adresini ve ISP bilgisini al (Yasal delil için)
            ip_info = get_real_ip_with_isp(request)
            print(f"[PDF] IP Bilgileri: {ip_info['ip']} - {ip_info['isp']}")
            
            # PDF'i kim işledi? (Onaylayan/Reddeden)
            action_user = mutabakat.receiver if mutabakat.durum in [MutabakatDurumu.ONAYLANDI, MutabakatDurumu.REDDEDILDI] else current_user
            action = 'ONAYLANDI' if mutabakat.durum == MutabakatDurumu.ONAYLANDI else 'REDDEDİLDİ'
            
            # Şirket bilgilerini al (logo için)
            company = db.query(Company).filter(Company.id == mutabakat.company_id).first()
            
            pdf_bytes = create_mutabakat_pdf(
                mutabakat=mutabakat,
                user=action_user,
                ip_info=ip_info,  # ISP bilgili IP (yasal delil için)
                action=action,
                red_nedeni=mutabakat.red_nedeni if action == 'REDDEDİLDİ' else None,
                company=company  # Şirket logosu için
            )
            
            # PDF'i kaydet
            pdf_dir = "pdfs/mutabakat"
            os.makedirs(pdf_dir, exist_ok=True)
            
            status_suffix = "ONAY" if mutabakat.durum == MutabakatDurumu.ONAYLANDI else "RED"
            pdf_filename = f"{mutabakat.mutabakat_no}_{status_suffix}_{get_turkey_time().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(pdf_dir, pdf_filename)
            
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
            
            # Dijital imza ekle (şirket sertifikası ile)
            print(f"[PDF] Dijital imza ekleniyor: {pdf_path}")
            
            # Şirket bilgilerini al
            company = db.query(Company).filter(Company.id == mutabakat.company_id).first()
            
            if company and company.certificate_path:
                # Şirketin kendi sertifikası ile imzala
                signed_pdf_path = pdf_signer.sign_pdf(
                    input_pdf_path=pdf_path,
                    company_name=company.full_company_name or company.company_name,
                    cert_path=company.certificate_path,
                    cert_password=company.certificate_password
                )
            else:
                # Fallback: Default Dino sertifikası
                print("[PDF] Sirket sertifikasi bulunamadi, default sertifika kullaniliyor")
                signed_pdf_path = pdf_signer.sign_pdf(pdf_path)
            
            # PDF izinlerini uygula (yazdirma ve imzalama haric digerleri engellenir)
            print(f"[PDF] Izinler uygulanıyor: {signed_pdf_path}")
            final_pdf_path = apply_pdf_permissions(signed_pdf_path)
            
            mutabakat.pdf_file_path = final_pdf_path
            db.commit()
            
        except Exception as e:
            import traceback
            error_detail = f"PDF oluşturulurken hata oluştu: {str(e)}"
            print(f"[PDF ERROR] {error_detail}")
            print(f"[PDF ERROR] Traceback:")
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_detail
            )
    
    # PDF'i döndür
    return FileResponse(
        path=mutabakat.pdf_file_path,
        media_type='application/pdf',
        filename=os.path.basename(mutabakat.pdf_file_path)
    )

@router.delete("/{mutabakat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mutabakat(
    mutabakat_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mutabakatı sil (sadece taslak olanlar)"""
    
    mutabakat = db.query(Mutabakat).filter(Mutabakat.id == mutabakat_id).first()
    
    if not mutabakat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mutabakat bulunamadı"
        )
    
    if mutabakat.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu mutabakatı silme yetkiniz yok"
        )
    
    if mutabakat.durum != MutabakatDurumu.TASLAK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece taslak mutabakatlar silinebilir"
        )
    
    db.delete(mutabakat)
    db.commit()
    
    return None

@router.post("/create-by-vkn-manual", response_model=MutabakatResponse, status_code=status.HTTP_201_CREATED)
def create_mutabakat_by_vkn_manual(
    payload: ManualMutabakatCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    VKN bazlı manuel mutabakat oluştur - Her bayi için borç/alacak girilir
    """
    from datetime import datetime
    
    # VKN + company_id ile kullanıcıyı bul
    receiver = db.query(User).filter(
        User.vkn_tckn == payload.receiver_vkn,
        User.company_id == current_user.company_id
    ).first()
    
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bu VKN'ye ait kullanıcı bulunamadı: {payload.receiver_vkn}"
        )
    
    if receiver.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kendinize mutabakat gönderemezsiniz"
        )
    
    # Tarihleri parse et
    donem_baslangic_dt = datetime.fromisoformat(payload.donem_baslangic.replace('Z', '+00:00'))
    donem_bitis_dt = datetime.fromisoformat(payload.donem_bitis.replace('Z', '+00:00'))
    
    # Bakiye hesapla
    bakiye = payload.toplam_alacak - payload.toplam_borc
    
    # Mutabakat oluştur
    db_mutabakat = Mutabakat(
        company_id=current_user.company_id,
        mutabakat_no=generate_mutabakat_no(),
        sender_id=current_user.id,
        receiver_id=receiver.id,
        receiver_vkn=payload.receiver_vkn,
        donem_baslangic=donem_baslangic_dt,
        donem_bitis=donem_bitis_dt,
        toplam_borc=payload.toplam_borc,
        toplam_alacak=payload.toplam_alacak,
        bakiye=bakiye,
        toplam_bayi_sayisi=len(payload.bayiler) if payload.bayiler else 0,
        aciklama=payload.aciklama or f"{receiver.company_name or payload.receiver_vkn} - Manuel Mutabakat",
        durum=MutabakatDurumu.TASLAK
    )
    
    db.add(db_mutabakat)
    db.flush()  # ID'yi al
    
    # Bayi detaylarını ekle
    if payload.bayiler:
        for bayi_data in payload.bayiler:
            bayi = db.query(Bayi).filter(Bayi.id == bayi_data['bayi_id']).first()
            if bayi:
                bayi_detay = MutabakatBayiDetay(
                    mutabakat_id=db_mutabakat.id,
                    bayi_kodu=bayi.bayi_kodu,
                    bayi_adi=bayi.bayi_adi,
                    bakiye=bayi_data.get('alacak', 0) - bayi_data.get('borc', 0)
                )
                db.add(bayi_detay)
    
    db.commit()
    db.refresh(db_mutabakat)
    
    # Activity log
    ip_info = get_real_ip_with_isp(request)
    ActivityLogger.log_mutabakat_created(
        db=db,
        user_id=current_user.id,
        mutabakat_no=db_mutabakat.mutabakat_no,
        ip_info=ip_info
    )
    
    return db_mutabakat

@router.post("/create-by-vkn", response_model=MutabakatResponse, status_code=status.HTTP_201_CREATED)
def create_mutabakat_by_vkn(
    vkn_tckn: str,
    donem: str,  # YYYY-MM format
    aciklama: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    VKN bazlı mutabakat oluştur - tüm bayileri içerir
    
    Args:
        vkn_tckn: Vergi Kimlik No veya TC Kimlik No
        donem: Dönem (YYYY-MM formatında, örn: 2025-10)
        aciklama: Açıklama (opsiyonel)
    """
    
    # VKN'ye göre kullanıcıyı bul
    receiver = db.query(User).filter(User.vkn_tckn == vkn_tckn).first()
    
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bu VKN'ye ait kullanıcı bulunamadı: {vkn_tckn}"
        )
    
    if receiver.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kendinize mutabakat gönderemezsiniz"
        )
    
    # VKN'ye ait bayileri getir
    bayiler = db.query(Bayi).filter(
        Bayi.vkn_tckn == vkn_tckn,
        Bayi.donem == donem
    ).all()
    
    if not bayiler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bu VKN'ye ait bayi bulunamadı (Dönem: {donem})"
        )
    
    # Toplam bakiyeleri hesapla
    toplam_bakiye = sum(b.bakiye for b in bayiler)
    toplam_borc = sum(b.bakiye for b in bayiler if b.bakiye > 0)
    toplam_alacak = abs(sum(b.bakiye for b in bayiler if b.bakiye < 0))
    
    # Dönem başlangıç ve bitiş tarihlerini hesapla (YYYY-MM formatından)
    from datetime import datetime, timedelta
    year, month = map(int, donem.split('-'))
    donem_baslangic = datetime(year, month, 1)  # datetime.date -> datetime.datetime
    
    # Ay sonunu hesapla
    if month == 12:
        donem_bitis = datetime(year, month, 31, 23, 59, 59)  # datetime.date -> datetime.datetime
    else:
        donem_bitis = datetime(year, month + 1, 1)
        # Bir gün geriye git ve saat 23:59:59 yap
        donem_bitis = donem_bitis - timedelta(days=1)
        donem_bitis = donem_bitis.replace(hour=23, minute=59, second=59)
    
    # Mutabakat oluştur
    db_mutabakat = Mutabakat(
        mutabakat_no=generate_mutabakat_no(),
        sender_id=current_user.id,
        receiver_id=receiver.id,
        receiver_vkn=vkn_tckn,
        donem_baslangic=donem_baslangic,
        donem_bitis=donem_bitis,
        toplam_borc=toplam_borc,
        toplam_alacak=toplam_alacak,
        bakiye=toplam_bakiye,
        toplam_bayi_sayisi=len(bayiler),
        aciklama=aciklama or f"{receiver.company_name or vkn_tckn} - {donem} Dönemi Mutabakat",
        durum=MutabakatDurumu.TASLAK
    )
    
    db.add(db_mutabakat)
    db.flush()  # ID'yi al
    
    # Bayi detaylarını ekle
    for bayi in bayiler:
        bayi_detay = MutabakatBayiDetay(
            mutabakat_id=db_mutabakat.id,
            bayi_kodu=bayi.bayi_kodu,
            bayi_adi=bayi.bayi_adi,
            bakiye=bayi.bakiye
        )
        db.add(bayi_detay)
    
    db.commit()
    db.refresh(db_mutabakat)
    
    # Activity log
    ActivityLogger.log(
        db=db,
        action="MUTABAKAT_OLUSTUR_VKN",
        description=f"VKN bazlı mutabakat oluşturuldu: {db_mutabakat.mutabakat_no} (VKN: {vkn_tckn}, {len(bayiler)} bayi)",
        user_id=current_user.id,
        ip="127.0.0.1"  # ip_address -> ip
    )
    
    return db_mutabakat

