# -*- coding: utf-8 -*-
"""
Bermer şirketinin notification_email adresini kontrol et
"""
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

server = os.getenv('DB_SERVER')
database = os.getenv('DB_NAME')
username = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')

connection_string = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    f"TrustServerCertificate=yes;"
)

print("=" * 60)
print("BERMER ŞİRKETİ EMAIL KONTROLÜ")
print("=" * 60)

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Bermer şirketini bul
    cursor.execute("""
        SELECT id, vkn, company_name, notification_email 
        FROM companies 
        WHERE company_name LIKE '%Bermer%' OR vkn = '1660290656'
    """)
    
    row = cursor.fetchone()
    
    if row:
        print(f"\n[✓] Bermer şirketi bulundu:")
        print(f"    ID: {row[0]}")
        print(f"    VKN: {row[1]}")
        print(f"    Şirket Adı: {row[2]}")
        print(f"    Notification Email: {row[3] or 'YOK - AYARLANMAMIŞ'}")
        
        if not row[3]:
            print("\n[!] SORUN BULUNDU: notification_email alanı boş!")
            print("    Çözüm: Admin panelden şirket düzenleyip email adresini kaydedin.")
        else:
            print(f"\n[✓] Email adresi ayarlanmış: {row[3]}")
    else:
        print("\n[✗] Bermer şirketi bulunamadı!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n[HATA] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

