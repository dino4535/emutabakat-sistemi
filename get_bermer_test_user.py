# -*- coding: utf-8 -*-
"""
Bermer Test Sirketi A.S. kullanici bilgilerini getir
"""
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def get_user_info():
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
    
    print("=" * 70)
    print("BERMER TEST SIRKETI A.S. - LOGIN BILGILERI")
    print("=" * 70)
    print("")
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Bermer Test Sirketi kullanıcısını bul
        cursor.execute("""
            SELECT 
                u.id,
                u.vkn_tckn,
                u.username,
                u.full_name,
                u.company_name,
                u.email,
                u.phone,
                u.role,
                u.is_active,
                c.company_name as sirket_adi
            FROM users u
            LEFT JOIN companies c ON u.company_id = c.id
            WHERE u.company_name LIKE '%Bermer Test%'
            OR u.full_name LIKE '%Bermer Test%'
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("[UYARI] 'Bermer Test Sirketi A.S.' kullanicisi bulunamadi!")
            print("")
            print("Bermer sirketindeki tum kullanicilari gosterelim:")
            print("")
            
            cursor.execute("""
                SELECT 
                    u.id,
                    u.vkn_tckn,
                    u.username,
                    u.full_name,
                    u.company_name,
                    u.email,
                    u.phone,
                    u.role,
                    u.is_active,
                    c.company_name as sirket_adi
                FROM users u
                LEFT JOIN companies c ON u.company_id = c.id
                WHERE c.company_name LIKE '%Bermer%'
                ORDER BY u.id
            """)
            
            users = cursor.fetchall()
        
        if users:
            for i, user in enumerate(users, 1):
                print(f"[{i}] KULLANICI BILGILERI:")
                print("-" * 70)
                print(f"  ID: {user[0]}")
                print(f"  VKN/TCKN: {user[1]}")
                print(f"  Username: {user[2]}")
                print(f"  Tam Adi: {user[3]}")
                print(f"  Sirket Adi: {user[4]}")
                print(f"  Email: {user[5] or '(Yok)'}")
                print(f"  Telefon: {user[6] or '(Yok)'}")
                print(f"  Rol: {user[7]}")
                print(f"  Aktif: {'Evet' if user[8] else 'Hayir'}")
                print(f"  Bagli Sirket: {user[9]}")
                print("")
                print(f"  LOGIN BILGILERI:")
                print(f"  ==================")
                print(f"  Username: {user[1]}")  # VKN ile login
                print(f"  Sifre: {user[1][-6:]}")  # VKN'nin son 6 hanesi
                print("")
                print("=" * 70)
                print("")
        else:
            print("[HATA] Bermer sirketinde hic kullanici bulunamadi!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"[HATA] {e}")
        return False
    
    return True

if __name__ == "__main__":
    get_user_info()

