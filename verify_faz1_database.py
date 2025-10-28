# -*- coding: utf-8 -*-
"""
FAZ 1 Database Verification Script
Tüm gerekli kolon ve tabloları kontrol eder
Tarih: 27 Ekim 2025
"""
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def verify_database():
    """Faz 1 için gerekli tüm kolon ve tabloları kontrol et"""
    
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
    print("FAZ 1 DATABASE VERIFICATION")
    print("=" * 70)
    print(f"Server: {server}")
    print(f"Database: {database}")
    print("")
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # ============================================================
        # 1. FAILED LOGIN TRACKING KOLONLARI
        # ============================================================
        print("[1/3] Failed Login Tracking kolonları kontrol ediliyor...")
        print("-" * 70)
        
        required_user_columns = [
            ('failed_login_count', 'INT'),
            ('last_failed_login', 'DATETIME'),
            ('account_locked_until', 'DATETIME'),
            ('account_locked_reason', 'NVARCHAR')
        ]
        
        all_user_columns_exist = True
        for col_name, col_type in required_user_columns:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM sys.columns 
                WHERE object_id = OBJECT_ID(N'[dbo].[users]') 
                AND name = ?
            """, col_name)
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                print(f"  [OK] users.{col_name} - MEVCUT")
            else:
                print(f"  [EKSIK] users.{col_name} - EKSIK!")
                all_user_columns_exist = False
        
        print("")
        
        # ============================================================
        # 2. FAILED_LOGIN_ATTEMPTS TABLOSU
        # ============================================================
        print("[2/3] failed_login_attempts tablosu kontrol ediliyor...")
        print("-" * 70)
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM sys.tables 
            WHERE name = 'failed_login_attempts'
        """)
        table_exists = cursor.fetchone()[0] > 0
        
        if table_exists:
            print("  [OK] failed_login_attempts tablosu - MEVCUT")
            
            # Kolon sayısını kontrol et
            cursor.execute("""
                SELECT COUNT(*) 
                FROM sys.columns 
                WHERE object_id = OBJECT_ID(N'[dbo].[failed_login_attempts]')
            """)
            col_count = cursor.fetchone()[0]
            print(f"  [OK] Toplam {col_count} kolon var")
            
            # Index sayısını kontrol et
            cursor.execute("""
                SELECT COUNT(*) 
                FROM sys.indexes 
                WHERE object_id = OBJECT_ID(N'[dbo].[failed_login_attempts]')
                AND name IS NOT NULL
            """)
            idx_count = cursor.fetchone()[0]
            print(f"  [OK] Toplam {idx_count} index var")
        else:
            print("  [EKSIK] failed_login_attempts tablosu - EKSIK!")
        
        print("")
        
        # ============================================================
        # 3. DATABASE INDEXLER
        # ============================================================
        print("[3/3] Kritik index'ler kontrol ediliyor...")
        print("-" * 70)
        
        critical_indexes = [
            ('users', 'idx_users_vkn_company'),
            ('users', 'idx_users_company'),
            ('mutabakats', 'idx_mutabakat_company_durum'),
            ('mutabakats', 'idx_mutabakat_no'),
            ('bayiler', 'idx_bayiler_user'),
            ('failed_login_attempts', 'idx_failed_login_vkn'),
            ('failed_login_attempts', 'idx_failed_login_user'),
        ]
        
        index_count = 0
        for table_name, index_name in critical_indexes:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM sys.indexes 
                WHERE object_id = OBJECT_ID(N'[dbo].[{}]')
                AND name = ?
            """.format(table_name), index_name)
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                print(f"  [OK] {table_name}.{index_name}")
                index_count += 1
            else:
                print(f"  [UYARI] {table_name}.{index_name} - EKSIK (opsiyonel)")
        
        print("")
        print("=" * 70)
        
        # ============================================================
        # OZET
        # ============================================================
        if all_user_columns_exist and table_exists:
            print("[OK] TUM GEREKLI KOLONLAR VE TABLOLAR MEVCUT!")
            print(f"[OK] {index_count}/{len(critical_indexes)} kritik index mevcut")
            print("")
            print("Sistem hazir! Backend yeniden baslatildiginda sorunsuz calisacak.")
        else:
            print("[EKSIK] EKSIK KOLONLAR/TABLOLAR VAR!")
            print("")
            print("Su komutu calistirin:")
            print("  python apply_failed_login_migration.py")
        
        print("=" * 70)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"[HATA] {e}")
        return False
    
    return True

if __name__ == "__main__":
    verify_database()

