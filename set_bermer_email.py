# -*- coding: utf-8 -*-
"""
Bermer şirketinin notification_email adresini ayarla
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
print("BERMER ŞİRKETİ EMAIL AYARLAMA")
print("=" * 60)

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Bermer'in email adresini güncelle
    cursor.execute("""
        UPDATE companies 
        SET notification_email = 'info@dinogida.com.tr'
        WHERE vkn = '1660290656'
    """)
    
    rows_affected = cursor.rowcount
    conn.commit()
    
    print(f"\n[✓] Bermer şirketi güncellendi")
    print(f"    Etkilenen kayıt: {rows_affected}")
    print(f"    Email: info@dinogida.com.tr")
    
    # Dino Gıda'nın da email adresini ayarla
    cursor.execute("""
        UPDATE companies 
        SET notification_email = 'info@dinogida.com.tr'
        WHERE vkn = '4640067727'
    """)
    
    rows_affected = cursor.rowcount
    conn.commit()
    
    print(f"\n[✓] Dino Gıda şirketi güncellendi")
    print(f"    Etkilenen kayıt: {rows_affected}")
    print(f"    Email: info@dinogida.com.tr")
    
    # Kontrol et
    cursor.execute("""
        SELECT company_name, vkn, notification_email 
        FROM companies 
        WHERE vkn IN ('1660290656', '4640067727')
    """)
    
    print("\n" + "=" * 60)
    print("GÜNCEL DURUM:")
    print("=" * 60)
    
    for row in cursor.fetchall():
        print(f"\n{row[0]}")
        print(f"  VKN: {row[1]}")
        print(f"  Email: {row[2]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("[✓] EMAIL ADRESLERI AYARLANDI!")
    print("=" * 60)
    print("\nArtık mutabakat onaylandığında/reddedildiğinde")
    print("info@dinogida.com.tr adresine email gönderilecek.")
    
except Exception as e:
    print(f"\n[HATA] {e}")
    import traceback
    traceback.print_exc()

