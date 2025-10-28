# -*- coding: utf-8 -*-
"""
Tum kullanıcıların sifrelerini VKN/TC'nin son 6 karakteri olarak guncelle
"""
import pyodbc
from dotenv import load_dotenv
import os
import bcrypt

# .env dosyasını yükle
load_dotenv()

# Veritabanı bağlantısı
def get_db_connection():
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    
    conn_str = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password}'
    )
    
    return pyodbc.connect(conn_str)


def reset_all_passwords():
    """Tum kullanıcıların sifrelerini VKN/TC'nin son 6 karakteri olarak guncelle"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("="*60)
        print("TUM KULLANICI SIFRELERINI SIFIRLAMA")
        print("="*60)
        
        # Tum kullanıcıları al (admin haric)
        cursor.execute("""
            SELECT id, username, vkn_tckn, full_name, role
            FROM users
            WHERE role NOT IN ('ADMIN')
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("[i] Guncellenecek kullanici bulunamadi")
            return
        
        print(f"\n[*] Toplam {len(users)} kullanici bulundu")
        print("[*] Sifreler VKN/TC'nin son 6 karakteri olarak ayarlanacak")
        print()
        
        basarili = 0
        basarisiz = 0
        hatalar = []
        
        for user in users:
            user_id, username, vkn_tckn, full_name, role = user
            
            try:
                if not vkn_tckn or len(vkn_tckn) < 6:
                    hatalar.append({
                        "username": username,
                        "hata": f"VKN/TC cok kisa veya bos: {vkn_tckn}"
                    })
                    basarisiz += 1
                    continue
                
                # VKN/TC'nin son 6 karakteri
                new_password = vkn_tckn[-6:]
                
                # Sifreyi hashle
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                # Sifreyi guncelle
                cursor.execute("""
                    UPDATE users 
                    SET hashed_password = ?
                    WHERE id = ?
                """, (hashed_password, user_id))
                
                print(f"[OK] {username:30s} | VKN: {vkn_tckn:11s} | Sifre: {new_password} | {full_name[:40]}")
                basarili += 1
                
            except Exception as e:
                hatalar.append({
                    "username": username,
                    "hata": str(e)
                })
                basarisiz += 1
                print(f"[ERROR] {username:30s} | Hata: {str(e)}")
        
        # Commit
        conn.commit()
        
        print("\n" + "="*60)
        print("OZET")
        print("="*60)
        print(f"Toplam:    {len(users)}")
        print(f"Basarili:  {basarili}")
        print(f"Basarisiz: {basarisiz}")
        
        if hatalar:
            print("\nHATALAR:")
            for hata in hatalar:
                print(f"  - {hata['username']}: {hata['hata']}")
        
        print("\n[OK] TUM ISLEMLER TAMAMLANDI")
        print("="*60)
        print("\nNOT: Admin kullanicilarin sifreleri degistirilmedi")
        print("     Kullanicilar VKN/TC'lerinin son 6 hanesi ile giris yapabilir")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] HATA: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    reset_all_passwords()

