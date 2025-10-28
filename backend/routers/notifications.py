"""Bildirim Router - Gerçek zamanlı kullanıcı bildirimleri"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from backend.database import get_db
from backend.models import User, Mutabakat, MutabakatDurumu, UserRole
from backend.auth import get_current_active_user
from datetime import datetime, timedelta
from typing import List, Dict

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("/")
def get_notifications(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Dict]:
    """
    Kullanıcının rolüne göre bildirimleri getir
    - Admin/Muhasebe/Planlama: Taslak mutabakatlar, bekleyen onaylar
    - Müşteri: Onay bekleyen mutabakatlar
    """
    notifications = []
    
    # Müşteri bildirimleri
    if current_user.role in [UserRole.MUSTERI, UserRole.TEDARIKCI]:
        # 1. Onay bekleyen mutabakatlar
        pending_mutabakats = db.query(Mutabakat).filter(
            and_(
                Mutabakat.receiver_id == current_user.id,
                Mutabakat.durum == MutabakatDurumu.GONDERILDI
            )
        ).all()
        
        for mut in pending_mutabakats:
            # Gönderim tarihinden kaç gün geçti?
            days_ago = (datetime.utcnow() - mut.gonderim_tarihi).days if mut.gonderim_tarihi else 0
            
            # Gönderen bilgisi
            sender_name = "Bilinmeyen"
            if mut.sender:
                sender_name = mut.sender.company_name or mut.sender.full_name or mut.sender.username
            
            notifications.append({
                "id": f"mut-{mut.id}",
                "type": "pending_approval",
                "title": "Onay Bekleyen Mutabakat",
                "message": f"{sender_name} - {mut.mutabakat_no} ({days_ago} gün önce gönderildi)",
                "link": f"/mutabakat/{mut.id}",
                "date": mut.gonderim_tarihi.isoformat() if mut.gonderim_tarihi else datetime.utcnow().isoformat(),
                "priority": "high" if days_ago > 3 else "medium",
                "amount": abs(mut.bakiye)
            })
        
        # 2. Son 7 günde onayladığım mutabakatlar
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        approved_mutabakats = db.query(Mutabakat).filter(
            and_(
                Mutabakat.receiver_id == current_user.id,
                Mutabakat.durum == MutabakatDurumu.ONAYLANDI,
                Mutabakat.onay_tarihi >= one_week_ago
            )
        ).all()
        
        for mut in approved_mutabakats:
            # Gönderen bilgisi
            sender_name = "Bilinmeyen"
            if mut.sender:
                sender_name = mut.sender.company_name or mut.sender.full_name or mut.sender.username
            
            notifications.append({
                "id": f"approved-{mut.id}",
                "type": "approved",
                "title": "Mutabakat Onaylandı",
                "message": f"{sender_name} - {mut.mutabakat_no}",
                "link": f"/mutabakat/{mut.id}",
                "date": mut.onay_tarihi.isoformat() if mut.onay_tarihi else datetime.utcnow().isoformat(),
                "priority": "low",
                "status": "approved"
            })
        
        # 3. Son 7 günde reddettiğim mutabakatlar
        rejected_mutabakats = db.query(Mutabakat).filter(
            and_(
                Mutabakat.receiver_id == current_user.id,
                Mutabakat.durum == MutabakatDurumu.REDDEDILDI,
                Mutabakat.red_tarihi >= one_week_ago
            )
        ).all()
        
        for mut in rejected_mutabakats:
            # Gönderen bilgisi
            sender_name = "Bilinmeyen"
            if mut.sender:
                sender_name = mut.sender.company_name or mut.sender.full_name or mut.sender.username
            
            notifications.append({
                "id": f"rejected-{mut.id}",
                "type": "rejected",
                "title": "Mutabakat Reddedildi",
                "message": f"{sender_name} - {mut.mutabakat_no}",
                "link": f"/mutabakat/{mut.id}",
                "date": mut.red_tarihi.isoformat() if mut.red_tarihi else datetime.utcnow().isoformat(),
                "priority": "low",
                "status": "rejected"
            })
    
    # Admin/Muhasebe/Planlama bildirimleri (Multi-Company)
    else:
        # Multi-company filtreleme hazırla
        if current_user.role == UserRole.ADMIN:
            # Sistem admini: TÜM şirketlerin mutabakatlarını görebilir
            company_filter = True
        elif current_user.role in [UserRole.COMPANY_ADMIN, UserRole.MUHASEBE, UserRole.PLANLAMA]:
            # Şirket admini/Muhasebe/Planlama: Sadece kendi şirketinin mutabakatları
            company_filter = Mutabakat.company_id == current_user.company_id
        else:
            company_filter = Mutabakat.sender_id == current_user.id
        
        # 1. Taslak mutabakatlar (gönderilmemiş) - Multi-Company
        taslak_query = db.query(Mutabakat).filter(
            Mutabakat.durum == MutabakatDurumu.TASLAK,
            company_filter
        )
        
        # Sistem admini değilse, kendi gönderdiği taslaklarla sınırla
        if current_user.role != UserRole.ADMIN:
            taslak_query = taslak_query.filter(Mutabakat.sender_id == current_user.id)
        
        taslak_count = taslak_query.count()
        
        if taslak_count > 0:
            notifications.append({
                "id": "taslak-mutabakat",
                "type": "draft",
                "title": f"{taslak_count} Taslak Mutabakat",
                "message": f"Gönderilmeyi bekleyen {taslak_count} adet taslak mutabakat var",
                "link": "/mutabakat?durum=taslak",
                "date": datetime.utcnow().isoformat(),
                "priority": "low",
                "count": taslak_count
            })
        
        # 2. Son 7 günde gönderilen ama henüz onaylanmayan - Multi-Company
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        pending_query = db.query(Mutabakat).filter(
            Mutabakat.durum == MutabakatDurumu.GONDERILDI,
            Mutabakat.gonderim_tarihi >= one_week_ago,
            company_filter
        )
        
        # Sistem admini değilse, kendi gönderdiği mutabakatlarla sınırla
        if current_user.role != UserRole.ADMIN:
            pending_query = pending_query.filter(Mutabakat.sender_id == current_user.id)
        
        pending_mutabakats = pending_query.all()
        
        for mut in pending_mutabakats:
            days_waiting = (datetime.utcnow() - mut.gonderim_tarihi).days if mut.gonderim_tarihi else 0
            
            # Alıcı bilgisi
            receiver_name = "Bilinmeyen"
            if mut.receiver:
                receiver_name = mut.receiver.company_name or mut.receiver.full_name or mut.receiver.username
            
            notifications.append({
                "id": f"pending-{mut.id}",
                "type": "waiting_approval",
                "title": "Onay Bekleniyor",
                "message": f"{receiver_name} - {mut.mutabakat_no} ({days_waiting} gün)",
                "link": f"/mutabakat/{mut.id}",
                "date": mut.gonderim_tarihi.isoformat() if mut.gonderim_tarihi else datetime.utcnow().isoformat(),
                "priority": "high" if days_waiting > 5 else "medium",
                "days_waiting": days_waiting
            })
        
        # 3. Son 24 saatte onaylanan/reddedilen - Multi-Company
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_query = db.query(Mutabakat).filter(
            company_filter,
            or_(
                and_(
                    Mutabakat.durum == MutabakatDurumu.ONAYLANDI,
                    Mutabakat.onay_tarihi >= yesterday
                ),
                and_(
                    Mutabakat.durum == MutabakatDurumu.REDDEDILDI,
                    Mutabakat.red_tarihi >= yesterday
                )
            )
        )
        
        # Sistem admini değilse, kendi gönderdiği mutabakatlarla sınırla
        if current_user.role != UserRole.ADMIN:
            recent_query = recent_query.filter(Mutabakat.sender_id == current_user.id)
        
        recent_responses = recent_query.all()
        
        for mut in recent_responses:
            is_approved = mut.durum == MutabakatDurumu.ONAYLANDI
            response_date = mut.onay_tarihi if is_approved else mut.red_tarihi
            
            # Alıcı bilgisi
            receiver_name = "Bilinmeyen"
            if mut.receiver:
                receiver_name = mut.receiver.company_name or mut.receiver.full_name or mut.receiver.username
            
            notifications.append({
                "id": f"response-{mut.id}",
                "type": "approved" if is_approved else "rejected",
                "title": "✅ Onaylandı" if is_approved else "❌ Reddedildi",
                "message": f"{receiver_name} - {mut.mutabakat_no}",
                "link": f"/mutabakat/{mut.id}",
                "date": response_date.isoformat() if response_date else datetime.utcnow().isoformat(),
                "priority": "low",
                "status": "approved" if is_approved else "rejected"
            })
    
    # Tarihe göre sırala (en yeni önce)
    notifications.sort(key=lambda x: x['date'], reverse=True)
    
    return notifications

