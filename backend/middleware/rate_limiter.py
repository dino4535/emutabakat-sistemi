# -*- coding: utf-8 -*-
"""
API Rate Limiting Middleware
DOS/DDOS saldırılarına karşı koruma için endpoint bazlı rate limiting
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Callable
import time
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
from functools import wraps

# In-memory rate limit storage (production'da Redis kullanılmalı)
rate_limit_storage = defaultdict(lambda: {"count": 0, "reset_time": None})
rate_limit_lock = asyncio.Lock()


class RateLimiter:
    """
    Rate Limiting sınıfı
    
    Kullanım:
        @RateLimiter.limit(max_requests=5, window_seconds=60)
        async def endpoint():
            ...
    """
    
    def __init__(self):
        self.storage = rate_limit_storage
        self.lock = rate_limit_lock
    
    @staticmethod
    def limit(max_requests: int = 100, window_seconds: int = 60, key_func: Callable = None):
        """
        Rate limit decorator
        
        Args:
            max_requests: Zaman penceresi içinde izin verilen maksimum istek sayısı
            window_seconds: Zaman penceresi (saniye)
            key_func: Rate limit için kullanılacak key fonksiyonu (varsayılan: IP adresi)
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Request objesini bul
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if request is None:
                    # Request bulunamazsa rate limit uygulama
                    return await func(*args, **kwargs)
                
                # Rate limit key'i oluştur
                if key_func:
                    client_key = key_func(request)
                else:
                    # Varsayılan: IP adresi
                    client_key = request.client.host if request.client else "unknown"
                
                # Endpoint path'i ekle (farklı endpoint'ler için ayrı limitler)
                limit_key = f"{client_key}:{request.url.path}"
                
                # Rate limit kontrolü
                async with rate_limit_lock:
                    now = datetime.now()
                    client_data = rate_limit_storage[limit_key]
                    
                    # Reset zamanı geçmişse sıfırla
                    if client_data["reset_time"] is None or now >= client_data["reset_time"]:
                        client_data["count"] = 0
                        client_data["reset_time"] = now + timedelta(seconds=window_seconds)
                    
                    # İstek sayısını artır
                    client_data["count"] += 1
                    current_count = client_data["count"]
                    reset_time = client_data["reset_time"]
                    
                    # Limit aşıldı mı?
                    if current_count > max_requests:
                        # Kalan süreyi hesapla
                        remaining_seconds = int((reset_time - now).total_seconds())
                        
                        # Rate limit aşımı error'u
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail={
                                "error": "Rate limit exceeded",
                                "message": f"Too many requests. Please try again in {remaining_seconds} seconds.",
                                "retry_after": remaining_seconds,
                                "limit": max_requests,
                                "window": window_seconds
                            },
                            headers={
                                "X-RateLimit-Limit": str(max_requests),
                                "X-RateLimit-Remaining": "0",
                                "X-RateLimit-Reset": str(int(reset_time.timestamp())),
                                "Retry-After": str(remaining_seconds)
                            }
                        )
                    
                    # Rate limit bilgilerini response header'larına ekle
                    remaining = max_requests - current_count
                    
                    # Normal akış
                    result = await func(*args, **kwargs)
                    
                    # Response'a header'ları ekle
                    if hasattr(result, 'headers'):
                        result.headers["X-RateLimit-Limit"] = str(max_requests)
                        result.headers["X-RateLimit-Remaining"] = str(remaining)
                        result.headers["X-RateLimit-Reset"] = str(int(reset_time.timestamp()))
                    
                    return result
            
            return wrapper
        return decorator
    
    @staticmethod
    async def clear_storage():
        """
        Rate limit storage'ı temizle (test için)
        """
        async with rate_limit_lock:
            rate_limit_storage.clear()


# Kullanıcı bazlı rate limit key fonksiyonu
def get_user_key(request: Request) -> str:
    """
    Kullanıcı ID'si varsa kullanıcı bazlı, yoksa IP bazlı key döndür
    """
    # Authorization header'dan user bilgisi al (varsa)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        # Token'dan user ID'si çıkarılabilir (şimdilik IP kullanıyoruz)
        pass
    
    # IP adresi
    return request.client.host if request.client else "unknown"


# Önceden tanımlı rate limit kuralları
class RateLimitRules:
    """
    Endpoint bazlı rate limit kuralları
    """
    
    # Login endpoint: Brute force koruması
    LOGIN = {"max_requests": 5, "window_seconds": 60}  # 5 istek/dakika
    
    # Genel API endpoint'leri
    API_DEFAULT = {"max_requests": 100, "window_seconds": 60}  # 100 istek/dakika
    
    # PDF download: Ağır işlem
    PDF_DOWNLOAD = {"max_requests": 10, "window_seconds": 60}  # 10 istek/dakika
    
    # Excel upload: Çok ağır işlem
    EXCEL_UPLOAD = {"max_requests": 5, "window_seconds": 300}  # 5 istek/5 dakika
    
    # Mutabakat oluşturma
    MUTABAKAT_CREATE = {"max_requests": 20, "window_seconds": 60}  # 20 istek/dakika
    
    # Kullanıcı oluşturma
    USER_CREATE = {"max_requests": 10, "window_seconds": 60}  # 10 istek/dakika
    
    # Dashboard: Sık erişilen ama ağır sorgu
    DASHBOARD = {"max_requests": 30, "window_seconds": 60}  # 30 istek/dakika
    
    # KVKK onayı
    KVKK_CONSENT = {"max_requests": 10, "window_seconds": 300}  # 10 istek/5 dakika


# Rate limit exception handler
async def rate_limit_exception_handler(request: Request, exc: HTTPException):
    """
    Rate limit aşımı için özel error handler
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path),
            "method": request.method
        },
        headers=exc.headers or {}
    )


# Cleanup task (eski rate limit kayıtlarını temizle)
async def cleanup_rate_limit_storage():
    """
    Her 1 saatte bir eski rate limit kayıtlarını temizle
    """
    while True:
        await asyncio.sleep(3600)  # 1 saat bekle
        
        async with rate_limit_lock:
            now = datetime.now()
            keys_to_delete = []
            
            for key, data in rate_limit_storage.items():
                # Reset zamanı geçmişse sil
                if data["reset_time"] and now >= data["reset_time"] + timedelta(hours=1):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del rate_limit_storage[key]
            
            if keys_to_delete:
                print(f"[RATE_LIMIT] {len(keys_to_delete)} adet eski kayıt temizlendi")

