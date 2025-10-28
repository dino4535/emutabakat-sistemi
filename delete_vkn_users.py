# -*- coding: utf-8 -*-
"""
Belirtilen VKN'lere ait kullanici ve bayi kayitlarini sil
"""
import pyodbc
from dotenv import load_dotenv
import os

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


def delete_users_by_vkn(vkn_list):
    """VKN listesindeki kullanicilari ve iliskili bayileri sil"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for vkn in vkn_list:
            print(f"\n{'='*60}")
            print(f"VKN: {vkn}")
            print(f"{'='*60}")
            
            # Kullaniciyi bul
            cursor.execute("SELECT id, username, full_name, email FROM users WHERE vkn_tckn = ?", (vkn,))
            users = cursor.fetchall()
            
            if not users:
                print(f"[X] VKN {vkn} icin kullanici bulunamadi")
                continue
            
            for user in users:
                user_id, username, full_name, email = user
                print(f"\n[*] Kullanici bulundu:")
                print(f"   ID: {user_id}")
                print(f"   Username: {username}")
                print(f"   Ad Soyad: {full_name}")
                print(f"   Email: {email}")
                
                # Bu kullaniciya ait bayileri bul
                cursor.execute("SELECT COUNT(*) FROM bayiler WHERE user_id = ?", (user_id,))
                bayi_count = cursor.fetchone()[0]
                
                if bayi_count > 0:
                    print(f"\n[*] {bayi_count} adet bayi kaydi bulundu")
                    cursor.execute("SELECT bayi_kodu, bayi_adi FROM bayiler WHERE user_id = ?", (user_id,))
                    bayiler = cursor.fetchall()
                    for bayi_kodu, bayi_adi in bayiler:
                        print(f"   - {bayi_kodu}: {bayi_adi}")
                    
                    # Bayileri sil
                    cursor.execute("DELETE FROM bayiler WHERE user_id = ?", (user_id,))
                    print(f"[OK] {bayi_count} bayi kaydi silindi")
                else:
                    print("[i] Bu kullaniciya ait bayi kaydi yok")
                
                # KVKK consent kayitlarini sil
                cursor.execute("SELECT COUNT(*) FROM kvkk_consents WHERE user_id = ?", (user_id,))
                kvkk_count = cursor.fetchone()[0]
                if kvkk_count > 0:
                    cursor.execute("DELETE FROM kvkk_consents WHERE user_id = ?", (user_id,))
                    print(f"[OK] {kvkk_count} KVKK onay kaydi silindi")
                
                # Activity log kayitlarini sil
                cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE user_id = ?", (user_id,))
                activity_count = cursor.fetchone()[0]
                if activity_count > 0:
                    cursor.execute("DELETE FROM activity_logs WHERE user_id = ?", (user_id,))
                    print(f"[OK] {activity_count} aktivite log kaydi silindi")
                
                # Mutabakat kayitlarini kontrol et ve sil
                try:
                    # mutabakats tablosu
                    cursor.execute("""
                        SELECT COUNT(*) FROM mutabakats 
                        WHERE sender_id = ? OR receiver_id = ?
                    """, (user_id, user_id))
                    mutabakat_count = cursor.fetchone()[0]
                    
                    if mutabakat_count > 0:
                        print(f"[!] UYARI: {mutabakat_count} adet mutabakat kaydi bulundu")
                        # Mutabakatları sil
                        cursor.execute("""
                            DELETE FROM mutabakats 
                            WHERE sender_id = ? OR receiver_id = ?
                        """, (user_id, user_id))
                        print(f"[OK] {mutabakat_count} mutabakat kaydi silindi")
                except Exception as e:
                    # Mutabakat tablosu yoksa devam et
                    pass
                
                # Kullaniciyi sil
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                print(f"\n[OK] Kullanici silindi: {username}")
        
        # Degisiklikleri kaydet
        conn.commit()
        print("\n" + "="*60)
        print("[OK] TUM ISLEMLER BASARIYLA TAMAMLANDI")
        print("="*60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] HATA: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Silinecek VKN listesi
    vkn_list = [
        "0010600612",
        "0010871925",
        "0010962386",
        "0010978473",
        "0010996506",
        "0022301397",
        "0022779038",
        "0040063951",
        "0040374673",
        "0051341752",
        "0070617995",
        "0071106731",
        "0071530840",
        "0071564241"
    ]
    
    print("="*60)
    print("VKN BAZLI KULLANICI VE BAYİ SİLME İŞLEMİ")
    print("="*60)
    print(f"Toplam {len(vkn_list)} VKN için işlem yapılacak")
    print("\nSilinecek VKN'ler:")
    for vkn in vkn_list:
        print(f"  - {vkn}")
    print("\n[!] Islem baslatiliyor...")
    
    delete_users_by_vkn(vkn_list)

