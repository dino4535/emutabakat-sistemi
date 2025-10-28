"""
Application Configuration
Redis ve diğer ayarlar
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings"""
    
    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    
    # Cache TTL (Time To Live) - seconds
    CACHE_TTL_USER = 300  # 5 minutes
    CACHE_TTL_COMPANY = 600  # 10 minutes
    CACHE_TTL_DASHBOARD = 120  # 2 minutes
    CACHE_TTL_KVKK = 3600  # 1 hour
    CACHE_TTL_MUTABAKAT_LIST = 60  # 1 minute
    
    # Rate Limiting (existing)
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    
    # Database (existing - add if needed)
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    
    # Email (existing - add if needed)
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "E-Mutabakat Sistemi")

settings = Settings()

