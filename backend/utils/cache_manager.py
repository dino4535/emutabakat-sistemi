"""
Redis Cache Manager
Sık kullanılan verileri cache'lemek için utility
"""
from typing import Optional, Any, Callable
import json
import hashlib
from functools import wraps
from datetime import timedelta
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("[WARNING] redis paketi yuklu degil. 'pip install redis' ile yukleyin.")

from backend.config import settings

class CacheManager:
    """Redis Cache Manager"""
    
    def __init__(self):
        """Redis connection pool oluştur"""
        if not REDIS_AVAILABLE:
            self.redis_client = None
            self.enabled = False
            return
        
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            print("[OK] Redis cache baglantisi basarili")
        except Exception as e:
            print(f"[WARNING] Redis baglantisi basarisiz, cache devre disi: {e}")
            self.redis_client = None
            self.enabled = False
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Cache key oluştur"""
        # Args ve kwargs'ı hash'le
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"cache:{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Cache'den veri al"""
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Cache'e veri yaz (TTL saniye cinsinden)"""
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Cache'den veri sil"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Pattern'e uyan tüm key'leri sil"""
        if not self.enabled:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """Tüm cache'i temizle"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Key var mı kontrol et"""
        if not self.enabled:
            return False
        
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Key'in kalan TTL'ini al (saniye)"""
        if not self.enabled:
            return -1
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            print(f"Cache TTL error: {e}")
            return -1
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Counter artır"""
        if not self.enabled:
            return None
        
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            print(f"Cache increment error: {e}")
            return None
    
    def get_stats(self) -> dict:
        """Cache istatistikleri"""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info("stats")
            return {
                "enabled": True,
                "total_connections": info.get("total_connections_received", 0),
                "commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {"enabled": True, "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Cache hit rate hesapla"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# Global cache instance
cache_manager = CacheManager()


# Decorator for caching
def cached(prefix: str, ttl: int = 300):
    """
    Cache decorator
    
    Usage:
        @cached("user_profile", ttl=600)
        def get_user_profile(user_id: int):
            # ... expensive operation
            return user_data
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Cache key oluştur
            cache_key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # Cache'den dene
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Cache miss, fonksiyonu çalıştır
            result = func(*args, **kwargs)
            
            # Sonucu cache'e yaz
            if result is not None:
                cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Helper functions
def invalidate_user_cache(user_id: int):
    """Kullanıcı cache'ini temizle"""
    cache_manager.delete_pattern(f"cache:user_*:{user_id}*")


def invalidate_company_cache(company_id: int):
    """Şirket cache'ini temizle"""
    cache_manager.delete_pattern(f"cache:company_*:{company_id}*")


def invalidate_dashboard_cache(user_id: int = None, company_id: int = None):
    """Dashboard cache'ini temizle"""
    if user_id:
        cache_manager.delete_pattern(f"cache:dashboard_*:{user_id}*")
    if company_id:
        cache_manager.delete_pattern(f"cache:dashboard_*:{company_id}*")


def invalidate_mutabakat_cache():
    """Mutabakat cache'ini temizle"""
    cache_manager.delete_pattern("cache:mutabakat_*")

