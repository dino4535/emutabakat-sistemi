# -*- coding: utf-8 -*-
"""
Bermer şirketine notification email ekle
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

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Bermer şirketini bul
    cursor.execute("SELECT id, company_name, notification_email FROM companies WHERE vkn = '1660290656'")
    company = cursor.fetchone()
    
    if company:
        print(f"\n[OK] Bermer bulundu: {company.company_name}")
        print(f"    Mevcut email: {company.notification_email}")
        
        # Email güncelle
        cursor.execute("""
            UPDATE companies 
            SET notification_email = 'info@dinogida.com.tr'
            WHERE vkn = '1660290656'
        """)
        conn.commit()
        
        print(f"\n[OK] Bermer notification email guncellendi: info@dinogida.com.tr")
    else:
        print("[HATA] Bermer bulunamadi!")
    
    # Dino Gıda'yı da kontrol et
    cursor.execute("SELECT id, company_name, notification_email FROM companies WHERE vkn = '4640067727'")
    dino = cursor.fetchone()
    
    if dino:
        print(f"\n[OK] Dino Gida: {dino.company_name}")
        print(f"    Email: {dino.notification_email}")
        
        if not dino.notification_email:
            cursor.execute("""
                UPDATE companies 
                SET notification_email = 'info@dinogida.com.tr'
                WHERE vkn = '4640067727'
            """)
            conn.commit()
            print(f"[OK] Dino Gida notification email guncellendi: info@dinogida.com.tr")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("BASARILI!")
    print("=" * 60)
    print("\nArtik mutabakat onay/red bildirimleri")
    print("info@dinogida.com.tr adresine gidecek!")
    print("\nAMA: SMTP ayarlarini .env dosyasinda yapmaniz gerekiyor!")
    print("=" * 60)

except Exception as e:
    print(f"[HATA] {e}")

