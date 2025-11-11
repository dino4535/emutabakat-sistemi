"""
VAPID Keys Oluşturma Scripti
Web Push Notifications için VAPID (Voluntary Application Server Identification) keys oluşturur
"""
from py_vapid import Vapid01
import base64
import os


def generate_vapid_keys():
    """VAPID keys oluştur ve ekrana yazdır"""
    print("🔑 VAPID Keys oluşturuluyor...")
    
    # VAPID keys oluştur
    vapid = Vapid01()
    vapid.generate_keys()
    
    # Keys'i base64 formatında al
    private_key = vapid.private_key.private_bytes(
        encoding=base64.Encoding.DER,
        format=base64.PrivateFormat.PKCS8,
        encryption_algorithm=base64.NoEncryption()
    )
    private_key_b64 = base64.urlsafe_b64encode(private_key).decode('utf-8').rstrip('=')
    
    public_key = vapid.public_key.public_bytes(
        encoding=base64.Encoding.X962,
        format=base64.PublicFormat.UncompressedPoint
    )
    public_key_b64 = base64.urlsafe_b64encode(public_key).decode('utf-8').rstrip('=')
    
    print("\n✅ VAPID Keys oluşturuldu!\n")
    print("=" * 60)
    print("Aşağıdaki değerleri .env dosyanıza ekleyin:\n")
    print(f"VAPID_PRIVATE_KEY={private_key_b64}")
    print(f"VAPID_PUBLIC_KEY={public_key_b64}")
    print(f"VAPID_EMAIL=noreply@dinogida.com.tr")
    print("=" * 60)
    print("\n⚠️  ÖNEMLİ: Private key'i güvenli tutun ve asla commit etmeyin!")
    print("\n📝 Frontend'de kullanmak için public key'i kopyalayın:")
    print(f"\n{public_key_b64}\n")


if __name__ == "__main__":
    generate_vapid_keys()

