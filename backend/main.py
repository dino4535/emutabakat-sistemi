from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.database import init_db, engine
from backend.routers import auth, mutabakat, dashboard, users, users_excel, users_excel_vkn, bulk_mutabakat, public, reports, verification, bayi, notifications, kvkk, legal_reports, admin_companies, security
from backend.logger import logger
import os
from dotenv import load_dotenv

# Tüm modelleri import et (SQLAlchemy tablo oluşturması için)
# Bu sayede init_db() çağrıldığında tüm tablolar oluşturulur
import backend.models  # noqa: F401 - Tüm modelleri yükle (SMSVerificationLog dahil)

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "E-Mutabakat Sistemi"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="Modern ve Hukuka Uygun E-Mutabakat Yönetim Sistemi"
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da specific domainler belirtilmeli
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları ekle
app.include_router(public.router)  # Public endpoints (authentication yok)
app.include_router(verification.router)  # Dijital imza doğrulama (mahkeme/yasal)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(users_excel.router)  # Kullanıcı Excel işlemleri (Eski sistem)
app.include_router(users_excel_vkn.router)  # VKN Bazlı Toplu Kullanıcı ve Bayi Yükleme (YENİ)
app.include_router(bayi.router)  # Bayi yönetimi (VKN bazlı çoklu bayi)
app.include_router(mutabakat.router)
app.include_router(dashboard.router)
app.include_router(bulk_mutabakat.router)
app.include_router(reports.router)  # Admin raporları
app.include_router(notifications.router)  # Gerçek zamanlı bildirimler
app.include_router(kvkk.router)  # KVKK onayları ve metinleri
app.include_router(legal_reports.router)  # Yasal raporlar (resmi makamlar için)
app.include_router(admin_companies.router)  # Admin: Şirket yönetimi (Multi-Company)
app.include_router(security.router)  # Güvenlik yönetimi (Failed Login Tracking)

@app.on_event("startup")
async def startup_event():
    """Uygulama başlatma işlemleri"""
    logger.info("E-Mutabakat Sistemi başlatılıyor...")
    try:
        init_db()
        logger.info("Veritabanı bağlantısı başarılı")
    except Exception as e:
        logger.error(f"Veritabanı bağlantı hatası: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Uygulama kapatma işlemleri"""
    logger.info("E-Mutabakat Sistemi kapatılıyor...")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global hata yakalayıcı"""
    logger.error(f"Global hata: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Bir hata oluştu. Lütfen daha sonra tekrar deneyin."}
    )

@app.get("/")
def root():
    """Ana sayfa"""
    return {
        "message": "E-Mutabakat Sistemi API",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "docs": "/docs",
        "status": "active"
    }

@app.get("/health")
def health_check():
    """Sağlık kontrolü"""
    try:
        # Veritabanı bağlantısını test et
        engine.connect()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

