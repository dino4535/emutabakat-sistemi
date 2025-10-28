from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pyodbc
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Veritabanı bağlantı bilgileri
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

# SQL Server bağlantı URL'si - TCP/IP ile
# Port ekleyelim ve TrustServerCertificate=yes ekleyelim
from urllib.parse import quote_plus

# Şifreyi URL-safe encode edelim
password_encoded = quote_plus(DB_PASSWORD)

# Connection string parametreleri
connection_params = [
    f"DRIVER={{{DB_DRIVER}}}",
    f"SERVER={DB_SERVER},1433",  # Port ekle
    f"DATABASE={DB_NAME}",
    f"UID={DB_USER}",
    f"PWD={DB_PASSWORD}",
    "TrustServerCertificate=yes",
    "Connection Timeout=60",  # Timeout artırıldı (30 -> 60)
    "Encrypt=no"  # SSL şifreleme devre dışı (hız için)
]

connection_string = ";".join(connection_params)
DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string)}"

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
    logger.info(f"Server: {DB_SERVER}, Database: {DB_NAME}")
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

