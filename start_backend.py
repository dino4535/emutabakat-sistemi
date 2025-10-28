"""
Backend başlatma ve tablo oluşturma scripti
"""
import sys
import os

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("E-MUTABAKAT SISTEMI - BACKEND BASLATILIYOR")
print("=" * 60)
print()

# Environment variables yükle
from dotenv import load_dotenv
load_dotenv()

print("[OK] Environment variables yuklendi")
print()

# Veritabani baglantisini test et
print("Veritabani baglantisi test ediliyor...")
import time

max_retries = 3
retry_delay = 5  # saniye

for attempt in range(1, max_retries + 1):
    try:
        from backend.database import engine, init_db
        
        # Baglanti testi
        print(f"  Deneme {attempt}/{max_retries}...")
        with engine.connect() as conn:
            print("[OK] Veritabani baglantisi basarili!")
            print(f"  Server: {os.getenv('DB_SERVER')}")
            print(f"  Database: {os.getenv('DB_NAME')}")
            print()
        
        # Tablolari olustur
        print("Tablolar olusturuluyor...")
        init_db()
        print("[OK] Tablolar basariyla olusturuldu!")
        print()
        break  # Başarılı, döngüden çık
        
    except Exception as conn_error:
        if attempt < max_retries:
            print(f"[UYARI] Baglanti basarisiz (deneme {attempt}/{max_retries})")
            print(f"  Hata: {str(conn_error)[:100]}...")
            print(f"  {retry_delay} saniye sonra tekrar denenecek...")
            time.sleep(retry_delay)
        else:
            print(f"[HATA] {max_retries} deneme sonrası baglanti basarisiz!")
            raise conn_error

# PDF kolonu migration (for döngüsünden sonra)
print("Database migration kontrol ediliyor...")
try:
    from sqlalchemy import text
    with engine.connect() as conn:
        # pdf_file_path kolonu kontrol
        check_query = text("""
            SELECT COUNT(*) as count
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'mutabakats'
            AND COLUMN_NAME = 'pdf_file_path'
        """)
        result = conn.execute(check_query)
        exists = result.fetchone()[0] > 0
        
        if not exists:
            print("  pdf_file_path kolonu ekleniyor...")
            alter_query = text("""
                ALTER TABLE mutabakats
                ADD pdf_file_path NVARCHAR(255) NULL
            """)
            conn.execute(alter_query)
            conn.commit()
            print("[OK] pdf_file_path kolonu eklendi!")
        else:
            print("[OK] pdf_file_path kolonu zaten mevcut")
except Exception as e:
    print(f"[UYARI] Migration hatasi (devam ediliyor): {str(e)[:80]}...")
print()

# Olusturulan tablolari listele
print("Olusturulan tablolar:")
from backend.database import Base
for table in Base.metadata.tables.keys():
    print(f"  - {table}")
print()

print("=" * 60)
print("FastAPI sunucusu baslatiliyor...")
print("=" * 60)
print()
print("API: http://localhost:8000")
print("Docs: http://localhost:8000/docs")
print("Health: http://localhost:8000/health")
print()
print("Durdurmak icin CTRL+C")
print()

# FastAPI uygulamasını başlat
import uvicorn
from backend.main import app

uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    log_level="info"
)

