"""
Audit Log Tablosunu Oluşturma Script'i
SQLAlchemy kullanarak audit_logs tablosunu veritabanına ekler
"""

import sys
import os

# Backend modülünü import edebilmek için path ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.database import SessionLocal, engine
from backend.models import Base, AuditLog
from sqlalchemy import inspect


def create_audit_log_table():
    """Audit log tablosunu oluştur"""
    
    db = SessionLocal()
    
    try:
        print("🔍 Audit Log tablosu kontrol ediliyor...")
        
        # Tablo var mı kontrol et
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if 'audit_logs' in existing_tables:
            print("⚠️  'audit_logs' tablosu zaten mevcut!")
            
            # Tablo yapısını göster
            columns = inspector.get_columns('audit_logs')
            print(f"\n📋 Tablo Yapısı ({len(columns)} sütun):")
            for col in columns:
                print(f"   - {col['name']}: {col['type']}")
            
            response = input("\n❓ Tabloyu yeniden oluşturmak ister misiniz? (Tüm veriler silinir!) [y/N]: ")
            if response.lower() == 'y':
                print("🗑️  Mevcut tablo siliniyor...")
                AuditLog.__table__.drop(engine)
                print("✅ Tablo silindi")
            else:
                print("❌ İşlem iptal edildi")
                return
        
        # Tabloyu oluştur
        print("\n🔨 Audit Log tablosu oluşturuluyor...")
        Base.metadata.create_all(bind=engine, tables=[AuditLog.__table__])
        
        # Kontrol et
        inspector = inspect(engine)
        if 'audit_logs' in inspector.get_table_names():
            columns = inspector.get_columns('audit_logs')
            indexes = inspector.get_indexes('audit_logs')
            
            print(f"✅ 'audit_logs' tablosu başarıyla oluşturuldu!")
            print(f"   - {len(columns)} sütun")
            print(f"   - {len(indexes)} index")
            
            # Kayıt sayısını göster
            from sqlalchemy import text
            count = db.execute(text("SELECT COUNT(*) FROM audit_logs")).scalar()
            print(f"   - {count} kayıt")
            
            print("\n🎉 Audit Log sistemi hazır!")
            print("\n📚 Kullanım:")
            print("   from backend.utils.audit_logger import create_audit_log, log_login_attempt")
            print("   from backend.models import AuditLogAction")
            print()
            print("   # Login logla")
            print("   log_login_attempt(db, username='admin', success=True, ip_address='127.0.0.1', user_agent='...')")
            print()
            print("   # Mutabakat işlemi logla")
            print("   log_mutabakat_action(db, AuditLogAction.MUTABAKAT_CREATE, mutabakat, user)")
            
        else:
            print("❌ Tablo oluşturulamadı!")
            
    except Exception as e:
        print(f"❌ HATA: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("AUDIT LOG TABLO OLUŞTURMA")
    print("=" * 60)
    create_audit_log_table()

