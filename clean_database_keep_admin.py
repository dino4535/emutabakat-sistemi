#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Veritabanı Temizleme Scripti
Admin ve musteri1 kullanıcıları hariç tüm verileri sil
"""

from backend.database import SessionLocal
from backend.models import User, Bayi, Mutabakat
from sqlalchemy import text

def clean_database():
    db = SessionLocal()
    
    try:
        print("\n" + "="*60)
        print("VERITABANI TEMIZLIGI BASLIYOR")
        print("="*60)
        
        # 1. Korunacak kullanıcıları bul
        print("\n1. Korunacak kullanıcılar belirleniyor...")
        admin = db.query(User).filter(User.username == 'admin').first()
        musteri1 = db.query(User).filter(User.username == 'musteri1').first()
        
        keep_user_ids = []
        if admin:
            keep_user_ids.append(admin.id)
            print(f"   [+] Admin kullanicisi korunacak (ID: {admin.id})")
        else:
            print("   [!] Admin kullanicisi bulunamadi!")
            
        if musteri1:
            keep_user_ids.append(musteri1.id)
            print(f"   [+] Musteri1 kullanicisi korunacak (ID: {musteri1.id})")
        else:
            print("   [!] Musteri1 kullanicisi bulunamadi!")
        
        if not keep_user_ids:
            print("\n[X] Korunacak kullanici bulunamadi! Islem iptal ediliyor.")
            return
        
        # 2. Mevcut durumu göster
        print("\n2. Mevcut veritabanı durumu:")
        total_users = db.query(User).count()
        total_bayi = db.query(Bayi).count()
        total_mutabakat = db.query(Mutabakat).count()
        
        print(f"   - Kullanıcılar: {total_users}")
        print(f"   - Bayiler: {total_bayi}")
        print(f"   - Mutabakatlar: {total_mutabakat}")
        
        # 3. Activity log'ları temizle (önce bağımlılıklar) - HEPSİNİ SİL
        print("\n3. Tum activity loglari temizleniyor...")
        try:
            result = db.execute(text("DELETE FROM activity_logs"))
            db.commit()
            print(f"   [OK] {result.rowcount} log kaydi silindi")
        except Exception as e:
            print(f"   [!] Log temizleme hatasi (tablo olmayabilir): {e}")
            db.rollback()
        
        # 4. Tüm Mutabakatları sil
        print("\n4. Tum mutabakatlar siliniyor...")
        deleted_mutabakat = db.query(Mutabakat).delete()
        db.commit()
        print(f"   [OK] {deleted_mutabakat} mutabakat silindi")
        
        # 5. Tüm Bayileri sil
        print("\n5. Tum bayiler siliniyor...")
        deleted_bayi = db.query(Bayi).delete()
        db.commit()
        print(f"   [OK] {deleted_bayi} bayi silindi")
        
        # 6. Admin ve musteri1 dışındaki kullanıcıları sil
        print("\n6. Diger kullanicilar siliniyor...")
        deleted_users = db.query(User).filter(
            User.id.notin_(keep_user_ids)
        ).delete(synchronize_session=False)
        db.commit()
        print(f"   [OK] {deleted_users} kullanici silindi")
        
        # 7. Son durumu göster
        print("\n7. Temizlik sonrası durum:")
        final_users = db.query(User).count()
        final_bayi = db.query(Bayi).count()
        final_mutabakat = db.query(Mutabakat).count()
        
        print(f"   - Kullanıcılar: {final_users}")
        print(f"   - Bayiler: {final_bayi}")
        print(f"   - Mutabakatlar: {final_mutabakat}")
        
        print("\n" + "="*60)
        print("[OK] TEMIZLIK BASARIYLA TAMAMLANDI!")
        print("="*60)
        
        # Kalan kullanıcıları listele
        print("\nKalan kullanıcılar:")
        remaining_users = db.query(User).all()
        for user in remaining_users:
            print(f"   - {user.username} ({user.role})")
        
    except Exception as e:
        print(f"\n[X] HATA: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("\n[!] DIKKAT: Bu islem geri alinamaz!")
    print("Admin ve musteri1 kullanicilari haric TUM veriler silinecek.")
    
    response = input("\nDevam etmek istiyor musunuz? (EVET yazin): ")
    
    if response.strip().upper() == "EVET":
        clean_database()
    else:
        print("\n[X] Islem iptal edildi.")

