"""
SMS Verification Logs Tablosu Oluşturma Script (Python)
SQL Server'da tabloyu otomatik oluşturur
"""
import sys
from sqlalchemy import text
from backend.database import engine, SessionLocal
from backend.models import Base, SMSVerificationLog
from backend.logger import logger

def create_sms_log_table():
    """SMS Verification Logs tablosunu oluştur"""
    db = SessionLocal()
    try:
        # Tablonun var olup olmadığını kontrol et
        check_query = text("""
            SELECT COUNT(*) as count
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'sms_verification_logs'
        """)
        result = db.execute(check_query).fetchone()
        
        if result and result[0] > 0:
            logger.info("sms_verification_logs tablosu zaten mevcut.")
            return True
        
        # Tablo yoksa oluştur
        logger.info("sms_verification_logs tablosu oluşturuluyor...")
        
        # SQLAlchemy ile tablo oluştur (sadece bu tablo için)
        SMSVerificationLog.__table__.create(bind=engine, checkfirst=True)
        
        db.commit()
        logger.info("✅ sms_verification_logs tablosu başarıyla oluşturuldu!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Tablo oluşturma hatası: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = create_sms_log_table()
    sys.exit(0 if success else 1)

