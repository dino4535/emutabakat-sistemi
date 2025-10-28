# -*- coding: utf-8 -*-
"""
Email Servis Test - SMTP bağlantısını test et
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("EMAIL SERVIS TEST")
print("=" * 60)

# SMTP ayarlarını kontrol et
smtp_host = os.getenv('SMTP_HOST')
smtp_port = os.getenv('SMTP_PORT')
smtp_user = os.getenv('SMTP_USER')
smtp_password = os.getenv('SMTP_PASSWORD')
smtp_from = os.getenv('SMTP_FROM_EMAIL')

print(f"\nSMTP Ayarları:")
print(f"  Host: {smtp_host}")
print(f"  Port: {smtp_port}")
print(f"  User: {smtp_user}")
print(f"  Password: {'*' * len(smtp_password) if smtp_password else 'YOK'}")
print(f"  From: {smtp_from}")

if not all([smtp_host, smtp_port, smtp_user, smtp_password, smtp_from]):
    print("\n[HATA] SMTP ayarları eksik!")
    exit(1)

print("\n" + "=" * 60)
print("EMAIL GÖNDERME TESTI")
print("=" * 60)

# Email servisini test et
try:
    from backend.utils.email_service import email_service
    from datetime import datetime
    
    print("\n[1/2] Email servisi yüklendi")
    print(f"      Enabled: {email_service.enabled}")
    
    if not email_service.enabled:
        print("\n[HATA] Email servisi devre dışı!")
        exit(1)
    
    # Test email gönder
    print("\n[2/2] Test email gönderiliyor...")
    print(f"      Alıcı: info@dinogida.com.tr")
    
    result = email_service.send_mutabakat_approved(
        to_email='info@dinogida.com.tr',
        company_name='Bermer Test',
        customer_name='Test Müşteri',
        mutabakat_no='TEST-001',
        donem_baslangic=datetime(2025, 10, 1),
        donem_bitis=datetime(2025, 10, 31),
        toplam_borc=100000.0,
        toplam_alacak=50000.0,
        bakiye=50000.0,
        onay_tarihi=datetime.now()
    )
    
    if result:
        print("\n" + "=" * 60)
        print("[✓] EMAIL BAŞARIYLA GÖNDERİLDİ!")
        print("=" * 60)
        print("\ninfo@dinogida.com.tr adresini kontrol edin.")
    else:
        print("\n" + "=" * 60)
        print("[✗] EMAIL GÖNDERİLEMEDİ!")
        print("=" * 60)
        print("\nHata detayları için yukarıdaki mesajları kontrol edin.")
    
except Exception as e:
    print(f"\n[HATA] {e}")
    import traceback
    traceback.print_exc()
    exit(1)

