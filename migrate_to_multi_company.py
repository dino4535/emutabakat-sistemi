"""
Multi-Company Sistem Migration
===============================
Bu script mevcut sistemi multi-company (çok şirketli) sisteme dönüştürür.

Yapılanlar:
1. Companies tablosu oluşturulur
2. İlk company (Dino Gıda) kaydı eklenir
3. Diğer tablolara company_id kolonları eklenir
4. Mevcut tüm verilere company_id=1 atanır
5. Unique constraint'ler güncellenir (vkn_tckn + company_id)
"""

import sys
import os
from pathlib import Path

# Backend modülünü import edebilmek için path ayarla
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.database import DATABASE_URL, engine
from backend.models import Base, Company
from backend.kvkk_constants import (
    KVKK_POLICY_TEXT, KVKK_POLICY_VERSION,
    CUSTOMER_NOTICE_TEXT, CUSTOMER_NOTICE_VERSION,
    DATA_RETENTION_POLICY_TEXT, DATA_RETENTION_VERSION
)
from datetime import datetime
import pytz

TURKEY_TZ = pytz.timezone('Europe/Istanbul')

def get_turkey_time():
    return datetime.now(TURKEY_TZ)

def run_migration():
    """Migration'ı çalıştır"""
    
    print("\n" + "="*60)
    print("MULTI-COMPANY SYSTEM MIGRATION BAŞLIYOR")
    print("="*60 + "\n")
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # ADIM 1: Mevcut tablolarda company_id olup olmadığını kontrol et
        print("[ADIM 1] Mevcut yapı kontrol ediliyor...")
        
        result = session.execute(text("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'company_id'"))
        company_id_exists = result.scalar() > 0
        
        if company_id_exists:
            print("  [!] Migration daha önce çalıştırılmış. Atlanıyor.")
            confirm = input("  [?] Yine de devam etmek istiyor musunuz? (y/N): ")
            if confirm.lower() != 'y':
                print("  [!] Migration iptal edildi.")
                return
        else:
            print("  [OK] Sistem yeni migration'a hazır.")
        
        # ADIM 2: Tüm tabloları oluştur (companies tablosu dahil)
        print("\n[ADIM 2] Tablolar oluşturuluyor...")
        Base.metadata.create_all(bind=engine)
        print("  [OK] Tüm tablolar oluşturuldu/güncellendi.")
        
        # ADIM 3: İlk Company kaydını ekle (Dino Gıda)
        print("\n[ADIM 3] Dino Gıda şirketi ekleniyor...")
        
        existing_company = session.query(Company).filter_by(vkn="DINOGIDA01").first()
        if not existing_company:
            dino_company = Company(
                vkn="DINOGIDA01",
                company_name="Dino Gıda",
                full_company_name="Hüseyin ve İbrahim Kaplan Dino Gıda San. Tic. Ltd. Şti.",
                tax_office="Menderes",
                address="Görece Cumhuriyet Mah. Gülçırpı Cad. No:19, 35473 Menderes / İzmir",
                phone="0850 220 45 66",
                email="info@dinogida.com.tr",
                website="www.dinogida.com.tr",
                logo_path="frontend/public/dino-logo.png",
                primary_color="#667eea",
                secondary_color="#764ba2",
                sms_enabled=True,
                sms_provider="netgsm",
                sms_header="DINOGIDA",
                sms_username=os.getenv("SMS_USERNAME", ""),
                sms_password=os.getenv("SMS_PASSWORD", ""),
                sms_api_key=os.getenv("SMS_API_KEY", ""),
                kvkk_policy_text=KVKK_POLICY_TEXT,
                kvkk_policy_version=KVKK_POLICY_VERSION,
                customer_notice_text=CUSTOMER_NOTICE_TEXT,
                customer_notice_version=CUSTOMER_NOTICE_VERSION,
                data_retention_policy_text=DATA_RETENTION_POLICY_TEXT,
                data_retention_version=DATA_RETENTION_VERSION,
                is_active=True,
                created_at=get_turkey_time()
            )
            session.add(dino_company)
            session.commit()
            company_id = dino_company.id
            print(f"  [OK] Dino Gıda eklendi (ID: {company_id})")
        else:
            company_id = existing_company.id
            print(f"  [!] Dino Gıda zaten mevcut (ID: {company_id})")
        
        # ADIM 4: Mevcut tablolara company_id kolonlarını ekle (eğer yoksa)
        print("\n[ADIM 4] Tablolara company_id kolonları ekleniyor...")
        
        tables_to_migrate = [
            'users',
            'mutabakats',
            'kvkk_consents',
            'activity_logs'
        ]
        
        for table_name in tables_to_migrate:
            # Kolon var mı kontrol et
            result = session.execute(text(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                AND column_name = 'company_id'
            """))
            
            if result.scalar() == 0:
                print(f"  [+] {table_name} tablosuna company_id ekleniyor...")
                
                # Kolon ekle (nullable olarak) - SQL Server syntax
                session.execute(text(f"""
                    ALTER TABLE {table_name} 
                    ADD company_id INT NULL
                """))
                
                # Mevcut kayıtlara company_id=1 ata
                update_query = f"UPDATE {table_name} SET company_id = {company_id} WHERE company_id IS NULL"
                result = session.execute(text(update_query))
                affected = result.rowcount
                print(f"      [+] {affected} kayit guncellendi (company_id={company_id})")
                
                # activity_logs hariç diğerleri için NOT NULL yap - SQL Server syntax
                if table_name != 'activity_logs':
                    session.execute(text(f"""
                        ALTER TABLE {table_name} 
                        ALTER COLUMN company_id INT NOT NULL
                    """))
                    print(f"      [+] NOT NULL constraint eklendi")
                
                # Foreign key ekle
                session.execute(text(f"""
                    ALTER TABLE {table_name} 
                    ADD CONSTRAINT fk_{table_name}_company_id 
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                """))
                print(f"      [+] Foreign key eklendi")
                
                # Index ekle
                session.execute(text(f"""
                    CREATE INDEX idx_{table_name}_company_id 
                    ON {table_name}(company_id)
                """))
                print(f"      [+] Index eklendi")
                
                session.commit()
                print(f"  [OK] {table_name} başarıyla güncellendi")
            else:
                print(f"  [!] {table_name} zaten company_id kolonu var")
        
        # ADIM 5: Users tablosuna bayi_kodu kolonu ekle
        print("\n[ADIM 5] Users tablosuna bayi_kodu ekleniyor...")
        
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'bayi_kodu'
        """))
        
        if result.scalar() == 0:
            session.execute(text("""
                ALTER TABLE users 
                ADD bayi_kodu VARCHAR(50) NULL
            """))
            
            session.execute(text("""
                CREATE INDEX idx_users_bayi_kodu 
                ON users(bayi_kodu)
            """))
            
            session.commit()
            print("  [OK] bayi_kodu kolonu eklendi")
        else:
            print("  [!] bayi_kodu kolonu zaten var")
        
        # ADIM 6: Unique constraint'leri güncelle
        print("\n[ADIM 6] Unique constraint'ler güncelleniyor...")
        
        # users.vkn_tckn unique constraint'ini kaldır - SQL Server syntax
        print("  [~] users.vkn_tckn unique constraint kontrol ediliyor...")
        try:
            # SQL Server'da unique constraint'i bulmak için sys tablosunu kullan
            constraint_result = session.execute(text("""
                SELECT name FROM sys.indexes 
                WHERE object_id = OBJECT_ID('users') 
                AND is_unique = 1 
                AND name LIKE '%vkn_tckn%'
            """))
            constraint_name = constraint_result.scalar()
            if constraint_name:
                session.execute(text(f"ALTER TABLE users DROP CONSTRAINT {constraint_name}"))
                print(f"  [OK] users.vkn_tckn unique constraint kaldırıldı ({constraint_name})")
            else:
                print("  [!] users.vkn_tckn unique constraint bulunamadı (zaten yok)")
        except Exception as e:
            if "could not be found" in str(e).lower() or "does not exist" in str(e).lower():
                print("  [!] users.vkn_tckn unique constraint zaten yok")
            else:
                print(f"  [!] Hata (devam ediliyor): {e}")
        
        # users.email unique constraint'ini kaldır - SQL Server syntax
        print("  [~] users.email unique constraint kontrol ediliyor...")
        try:
            constraint_result = session.execute(text("""
                SELECT name FROM sys.indexes 
                WHERE object_id = OBJECT_ID('users') 
                AND is_unique = 1 
                AND name LIKE '%email%'
            """))
            constraint_name = constraint_result.scalar()
            if constraint_name:
                session.execute(text(f"ALTER TABLE users DROP CONSTRAINT {constraint_name}"))
                print(f"  [OK] users.email unique constraint kaldırıldı ({constraint_name})")
            else:
                print("  [!] users.email unique constraint bulunamadı (zaten yok)")
        except Exception as e:
            if "could not be found" in str(e).lower() or "does not exist" in str(e).lower():
                print("  [!] users.email unique constraint zaten yok")
            else:
                print(f"  [!] Hata (devam ediliyor): {e}")
        
        # Composite unique constraint ekle: (vkn_tckn + company_id) - SQL Server syntax
        print("  [~] users.vkn_tckn + company_id composite unique constraint ekleniyor...")
        try:
            session.execute(text("""
                CREATE UNIQUE INDEX idx_users_vkn_company 
                ON users(vkn_tckn, company_id)
            """))
            print("  [OK] Composite unique constraint eklendi")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                print("  [!] Composite unique constraint zaten var")
            else:
                print(f"  [!] Hata: {e}")
        
        session.commit()
        
        # ADIM 7: Özet
        print("\n" + "="*60)
        print("MIGRATION BAŞARIYLA TAMAMLANDI!")
        print("="*60)
        
        # İstatistikler
        user_count = session.execute(text("SELECT COUNT(*) FROM users")).scalar()
        mutabakat_count = session.execute(text("SELECT COUNT(*) FROM mutabakats")).scalar()
        kvkk_count = session.execute(text("SELECT COUNT(*) FROM kvkk_consents")).scalar()
        log_count = session.execute(text("SELECT COUNT(*) FROM activity_logs")).scalar()
        
        print(f"\n[ISTATISTIKLER]")
        print(f"  [*] Companies: 1 (Dino Gida)")
        print(f"  [*] Users: {user_count} (hepsi company_id={company_id})")
        print(f"  [*] Mutabakats: {mutabakat_count} (hepsi company_id={company_id})")
        print(f"  [*] KVKK Consents: {kvkk_count} (hepsi company_id={company_id})")
        print(f"  [*] Activity Logs: {log_count} (hepsi company_id={company_id})")
        
        print("\n[SIRA SIZDE]")
        print("  1. Backend'i yeniden başlatın")
        print("  2. Auth sistemini güncelleyin (JWT'ye company_id ekleyin)")
        print("  3. Tüm endpoint'lerde company_id filtresi ekleyin")
        print("  4. Frontend'e firma seçim ekranı ekleyin")
        print("\n")
        
    except Exception as e:
        print(f"\n[HATA] Migration başarısız: {e}")
        print("\n[ROLLBACK] Değişiklikler geri alınıyor...")
        session.rollback()
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        session.close()
    
    return True

if __name__ == "__main__":
    print("\n[!] ONEMLI UYARI [!]")
    print("="*60)
    print("Bu migration:")
    print("  - companies tablosunu olusturacak")
    print("  - Dino Gida sirketini ekleyecek")
    print("  - Tum tablolara company_id ekleyecek")
    print("  - Mevcut tum verilere company_id=1 atayacak")
    print("  - Unique constraint'leri guncelleyecek")
    print("\nMevcut verileriniz korunacak ama yine de:")
    print("  [?] Veritabani yedegi aldiniz mi?")
    print("="*60 + "\n")
    
    confirm = input("Devam etmek istiyor musunuz? (yes/no): ")
    
    if confirm.lower() in ['yes', 'y', 'evet', 'e']:
        success = run_migration()
        if success:
            print("\n[OK] Migration basariyla tamamlandi!")
            sys.exit(0)
        else:
            print("\n[HATA] Migration basarisiz!")
            sys.exit(1)
    else:
        print("\n[!] Migration iptal edildi.")
        sys.exit(0)

