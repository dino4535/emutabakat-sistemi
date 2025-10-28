"""
Activity Log tablosuna ISP bilgilerini ekle (Yasal delil için)
"""
from backend.database import engine
from sqlalchemy import text

def add_isp_columns():
    """Activity logs tablosuna ISP bilgileri kolonlarını ekle"""
    
    with engine.connect() as conn:
        try:
            # ISP kolonu ekle
            conn.execute(text("""
                IF NOT EXISTS (
                    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'activity_logs' AND COLUMN_NAME = 'isp'
                )
                BEGIN
                    ALTER TABLE activity_logs ADD isp NVARCHAR(255) NULL
                    PRINT '[OK] isp kolonu eklendi'
                END
                ELSE
                    PRINT '[INFO] isp kolonu zaten mevcut'
            """))
            
            # City kolonu ekle
            conn.execute(text("""
                IF NOT EXISTS (
                    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'activity_logs' AND COLUMN_NAME = 'city'
                )
                BEGIN
                    ALTER TABLE activity_logs ADD city NVARCHAR(255) NULL
                    PRINT '[OK] city kolonu eklendi'
                END
                ELSE
                    PRINT '[INFO] city kolonu zaten mevcut'
            """))
            
            # Country kolonu ekle
            conn.execute(text("""
                IF NOT EXISTS (
                    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'activity_logs' AND COLUMN_NAME = 'country'
                )
                BEGIN
                    ALTER TABLE activity_logs ADD country NVARCHAR(255) NULL
                    PRINT '[OK] country kolonu eklendi'
                END
                ELSE
                    PRINT '[INFO] country kolonu zaten mevcut'
            """))
            
            # Organization kolonu ekle
            conn.execute(text("""
                IF NOT EXISTS (
                    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'activity_logs' AND COLUMN_NAME = 'organization'
                )
                BEGIN
                    ALTER TABLE activity_logs ADD organization NVARCHAR(255) NULL
                    PRINT '[OK] organization kolonu eklendi'
                END
                ELSE
                    PRINT '[INFO] organization kolonu zaten mevcut'
            """))
            
            conn.commit()
            print("\n[SUCCESS] Activity log ISP kolonları başarıyla eklendi!")
            print("Artık tüm işlemlerde ISP bilgisi kaydedilecek.")
            
        except Exception as e:
            print(f"\n[ERROR] Hata: {e}")
            conn.rollback()

if __name__ == "__main__":
    print("=" * 60)
    print("ACTIVITY LOG - ISP BİLGİLERİ MİGRATION")
    print("=" * 60)
    add_isp_columns()
    print("=" * 60)

