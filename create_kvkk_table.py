"""
KVKK Consents Tablosunu Oluştur
"""
import pyodbc
from dotenv import load_dotenv
import os

load_dotenv()

# Database bağlantı bilgileri
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

connection_string = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD};"
    f"TrustServerCertificate=yes;"
)

print("=" * 60)
print("KVKK CONSENTS TABLOSU OLUSTURULUYOR")
print("=" * 60)

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Tablo var mı kontrol et
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = 'kvkk_consents'
    """)
    
    if cursor.fetchone()[0] > 0:
        print("[!] kvkk_consents tablosu zaten mevcut")
        print("\n[?] Tabloyu yeniden olusturmak ister misiniz? (UYARI: Mevcut veriler silinecek!)")
        choice = input("Devam etmek icin 'EVET' yazin: ")
        
        if choice.upper() != 'EVET':
            print("[X] Islem iptal edildi")
            exit(0)
        
        print("\n[*] Mevcut tablo siliniyor...")
        cursor.execute("DROP TABLE kvkk_consents")
        conn.commit()
        print("[OK] Tablo silindi")
    
    print("\n[*] kvkk_consents tablosu olusturuluyor...")
    
    create_table_sql = """
    CREATE TABLE kvkk_consents (
        id INT PRIMARY KEY IDENTITY(1,1),
        user_id INT NOT NULL,
        
        -- Onay Tipleri
        kvkk_policy_accepted BIT DEFAULT 0,
        customer_notice_accepted BIT DEFAULT 0,
        data_retention_accepted BIT DEFAULT 0,
        system_consent_accepted BIT DEFAULT 0,
        
        -- Onay Tarihleri
        kvkk_policy_date DATETIME2,
        customer_notice_date DATETIME2,
        data_retention_date DATETIME2,
        system_consent_date DATETIME2,
        
        -- ISP Bilgileri (Yasal Delil)
        ip_address NVARCHAR(50),
        isp NVARCHAR(255),
        city NVARCHAR(255),
        country NVARCHAR(255),
        organization NVARCHAR(255),
        user_agent NVARCHAR(500),
        
        -- Onay Versiyonlari
        kvkk_policy_version NVARCHAR(20) DEFAULT '1.0',
        customer_notice_version NVARCHAR(20) DEFAULT '1.0',
        data_retention_version NVARCHAR(20) DEFAULT '1.0',
        system_consent_version NVARCHAR(20) DEFAULT '1.0',
        
        created_at DATETIME2 DEFAULT GETDATE(),
        updated_at DATETIME2 DEFAULT GETDATE(),
        
        -- Foreign Key
        CONSTRAINT FK_kvkk_consents_users FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    
    cursor.execute(create_table_sql)
    conn.commit()
    print("[OK] Tablo basariyla olusturuldu!")
    
    # Index oluştur
    print("\n[*] Index'ler olusturuluyor...")
    cursor.execute("CREATE INDEX IX_kvkk_consents_user_id ON kvkk_consents(user_id)")
    conn.commit()
    print("[OK] Index'ler olusturuldu")
    
    # Tablo yapısını göster
    print("\n" + "=" * 60)
    print("TABLO YAPISI")
    print("=" * 60)
    
    cursor.execute("""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'kvkk_consents'
        ORDER BY ORDINAL_POSITION
    """)
    
    print(f"{'Kolon Adi':<35} {'Tip':<20} {'Null?':<8} {'Varsayilan'}")
    print("-" * 80)
    
    for row in cursor.fetchall():
        col_name, data_type, is_nullable, default = row
        default_val = str(default)[:20] if default else '-'
        print(f"{col_name:<35} {data_type:<20} {is_nullable:<8} {default_val}")
    
    print("\n" + "=" * 60)
    print("[OK] KVKK CONSENTS TABLOSU HAZIR!")
    print("=" * 60)
    print("\nOzet:")
    print("  [+] Tablo: kvkk_consents")
    print("  [+] 4 Onay Tipi (KVKK, Aydinlatma, Saklama, Sistem)")
    print("  [+] Her onay icin tarih kaydi")
    print("  [+] ISP bilgileri (IP, ISP, Sehir, Ulke, Org)")
    print("  [+] Versiyon takibi")
    print("  [+] Foreign Key: users(id)")
    print("\n[OK] Sistem hazir!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n[HATA] {e}")
    exit(1)

