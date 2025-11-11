"""
VAPID Keys Oluşturma Scripti
Web Push Notifications için VAPID (Voluntary Application Server Identification) keys oluşturur
"""
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


def _b64url(data: bytes) -> str:
    """Base64 URL-safe, padding'siz string döndür."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def generate_vapid_keys():
    """VAPID keys oluştur ve ekrana yazdır"""
    print("🔑 VAPID Keys oluşturuluyor...")

    # P-256 (secp256r1) anahtar çifti oluştur
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    # Private key: PKCS8 DER
    private_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    private_key_b64 = _b64url(private_der)

    # Public key: Uncompressed point (X9.62)
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    public_key_b64 = _b64url(public_bytes)

    print("\n✅ VAPID Keys oluşturuldu!\n")
    print("=" * 60)
    print("Aşağıdaki değerleri .env dosyanıza ekleyin:\n")
    print(f"VAPID_PRIVATE_KEY={private_key_b64}")
    print(f"VAPID_PUBLIC_KEY={public_key_b64}")
    print("VAPID_EMAIL=noreply@dinogida.com.tr")
    print("=" * 60)
    print("\n⚠️  ÖNEMLİ: Private key'i güvenli tutun ve asla commit etmeyin!")
    print("\n📝 Frontend'de kullanmak için public key'i kopyalayın:")
    print(f"\n{public_key_b64}\n")


if __name__ == "__main__":
    generate_vapid_keys()

