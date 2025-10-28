from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pyodbc
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Veritabanı bağlantı URL'si environment variable'dan al
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # SQL loglarını kapat (geliştirme için True yapabilirsiniz)
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,  # 1 saatte bir connection yenile
        connect_args={
            "timeout": 60  # Connect timeout artırıldı
        }
    )
    logger.info("Veritabanı motoru başarıyla oluşturuldu")
except Exception as e:
    logger.error(f"Veritabanı bağlantı hatası: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Veritabanı session'ı oluştur"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Veritabanı tablolarını oluştur"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Veritabanı tabloları başarıyla oluşturuldu")
    except Exception as e:
        logger.error(f"Tablo oluşturma hatası: {e}")
        raise

