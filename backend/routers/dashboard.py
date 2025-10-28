from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from backend.database import get_db
from backend.models import User, Mutabakat, MutabakatDurumu
from backend.schemas import DashboardStats
from backend.auth import get_current_active_user
from backend.middleware.rate_limiter import RateLimiter, RateLimitRules
from backend.utils.cache_manager import cache_manager

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStats)
@RateLimiter.limit(**RateLimitRules.DASHBOARD)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Dashboard istatistiklerini getir (cached)"""
    
    # Cache kontrolü (2 dakika TTL)
    cache_key = f"cache:dashboard_stats:{current_user.id}"
    cached_stats = cache_manager.get(cache_key)
    
    if cached_stats:
        return DashboardStats(**cached_stats)
    
    # Cache miss - hesapla
    # Kullanıcının tüm mutabakatları
    base_query = db.query(Mutabakat).filter(
        or_(
            Mutabakat.sender_id == current_user.id,
            Mutabakat.receiver_id == current_user.id
        )
    )
    
    # Toplam mutabakat sayısı
    toplam_mutabakat = base_query.count()
    
    # Bekleyen mutabakatlar (gönderilen)
    bekleyen_mutabakat = base_query.filter(
        Mutabakat.durum == MutabakatDurumu.GONDERILDI
    ).count()
    
    # Onaylanan mutabakatlar
    onaylanan_mutabakat = base_query.filter(
        Mutabakat.durum == MutabakatDurumu.ONAYLANDI
    ).count()
    
    # Reddedilen mutabakatlar
    reddedilen_mutabakat = base_query.filter(
        Mutabakat.durum == MutabakatDurumu.REDDEDILDI
    ).count()
    
    # Toplam borç ve alacak (onaylanan mutabakatlardan)
    onaylanan_mutabakats = base_query.filter(
        Mutabakat.durum == MutabakatDurumu.ONAYLANDI
    ).all()
    
    # Eğer onaylanan mutabakat varsa topla, yoksa 0
    if onaylanan_mutabakats:
        toplam_borc = sum(m.toplam_borc for m in onaylanan_mutabakats)
        toplam_alacak = sum(m.toplam_alacak for m in onaylanan_mutabakats)
    else:
        toplam_borc = 0.0
        toplam_alacak = 0.0
    
    stats = DashboardStats(
        toplam_mutabakat=toplam_mutabakat,
        bekleyen_mutabakat=bekleyen_mutabakat,
        onaylanan_mutabakat=onaylanan_mutabakat,
        reddedilen_mutabakat=reddedilen_mutabakat,
        toplam_borc=toplam_borc,
        toplam_alacak=toplam_alacak
    )
    
    # Cache'e kaydet (2 dakika TTL)
    cache_manager.set(cache_key, stats.dict(), ttl=120)
    
    return stats

