# -*- coding: utf-8 -*-
"""
Mutabakat bilgilerini kontrol et
"""
from backend.database import SessionLocal
from backend.models import Mutabakat, User, Company

mutabakat_no = "MUT-20251027140648-8HZT"

db = SessionLocal()

try:
    # Mutabakat bilgilerini getir
    mutabakat = db.query(Mutabakat).filter(Mutabakat.mutabakat_no == mutabakat_no).first()
    
    if mutabakat:
        sender = db.query(User).filter(User.id == mutabakat.sender_id).first()
        receiver = db.query(User).filter(User.id == mutabakat.receiver_id).first()
        company = db.query(Company).filter(Company.id == mutabakat.company_id).first()
        
        print("\n" + "="*60)
        print(f"MUTABAKAT BİLGİLERİ: {mutabakat_no}")
        print("="*60)
        print(f"\nMutabakat ID: {mutabakat.id}")
        print(f"Mutabakat No: {mutabakat.mutabakat_no}")
        
        print(f"\n--- GÖNDEREN ŞİRKET (Mutabakatı Oluşturan) ---")
        print(f"Company ID: {mutabakat.company_id}")
        print(f"Şirket Adı: {company.company_name if company else 'N/A'}")
        print(f"Şirket VKN: {company.vkn if company else 'N/A'}")
        
        print(f"\n--- GÖNDEREN KULLANICI (Sistemi Kullanan) ---")
        print(f"User ID: {mutabakat.sender_id}")
        print(f"Username: {sender.username if sender else 'N/A'}")
        print(f"Ad Soyad: {sender.full_name if sender else 'N/A'}")
        print(f"VKN/TC: {sender.vkn_tckn if sender else 'N/A'}")
        print(f"Rol: {sender.role.value if sender and sender.role else 'N/A'}")
        
        print(f"\n--- ALICI (Mutabakatı Onaylayan) ---")
        print(f"User ID: {mutabakat.receiver_id}")
        print(f"Username: {receiver.username if receiver else 'N/A'}")
        print(f"Ad Soyad: {receiver.full_name if receiver else 'N/A'}")
        print(f"VKN/TC: {receiver.vkn_tckn if receiver else 'N/A'}")
        print(f"Müşteri Firma: {receiver.company_name if receiver else 'N/A'}")
        print(f"Şirketi: {receiver.company.company_name if receiver and receiver.company else 'N/A'}")
        
        print(f"\n--- DURUM ---")
        print(f"Durum: {mutabakat.durum.value}")
        print(f"Gönderim Tarihi: {mutabakat.gonderim_tarihi}")
        print(f"Onay Tarihi: {mutabakat.onay_tarihi}")
        print(f"Toplam Borç: {mutabakat.toplam_borc:,.2f} TL")
        print(f"Toplam Alacak: {mutabakat.toplam_alacak:,.2f} TL")
        print(f"Bakiye: {mutabakat.bakiye:,.2f} TL")
        print("="*60 + "\n")
        
        print("\n🔍 ÖZET:")
        print(f"✅ Bu mutabakat {company.company_name if company else 'N/A'} şirketi tarafından oluşturuldu")
        print(f"✅ {receiver.company_name if receiver else receiver.full_name if receiver else 'N/A'} müşterisine gönderildi")
        print(f"✅ Durum: {mutabakat.durum.value}\n")
    else:
        print(f"\n{mutabakat_no} numaralı mutabakat bulunamadı!\n")
        
finally:
    db.close()
