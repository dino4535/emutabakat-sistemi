# -*- coding: utf-8 -*-
"""
Failed Login Tracking Migration Script
Tarih: 27 Ekim 2025
"""
import pyodbc
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

def run_migration():
    """Failed Login Tracking kolonlarını veritabanına ekle"""
    
    # Veritabanı bağlantı bilgileri
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
    
    print("============================================================")
    print("FAILED LOGIN TRACKING MIGRATION")
    print("============================================================")
    print(f"Server: {server}")
    print(f"Database: {database}")
    print("")
    
    try:
        # Bağlantı oluştur
        print("[1/3] Veritabanina baglaniliyor...")
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        print("[OK] Baglanti basarili")
        print("")
        
        # SQL dosyasını oku
        print("[2/3] Migration scripti okunuyor...")
        with open('add_failed_login_columns.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # SQL komutlarını çalıştır
        print("[3/3] Migration uygulanıyor...")
        print("")
        
        # SQL script'i GO ile ayır ve tek tek çalıştır
        commands = sql_script.split('GO')
        for i, command in enumerate(commands, 1):
            command = command.strip()
            if command:
                try:
                    cursor.execute(command)
                    # PRINT mesajlarını göster
                    while cursor.nextset():
                        pass
                    for message in cursor.messages:
                        print(f"  {message[1]}")
                    conn.commit()
                except Exception as e:
                    print(f"  [UYARI] Komut {i}: {str(e)}")
        
        print("")
        print("============================================================")
        print("[OK] Migration basariyla tamamlandi!")
        print("============================================================")
        print("")
        print("Simdi backend'i yeniden baslatabilirsiniz:")
        print("  python start_backend.py")
        print("")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"[HATA] Migration basarisiz: {e}")
        return False
    
    return True

if __name__ == "__main__":
    run_migration()

