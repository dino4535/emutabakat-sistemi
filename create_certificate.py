"""
Self-Signed Dijital İmza Sertifikası Oluşturma
Bu script, PDF dijital imzalama için gerekli sertifikayı oluşturur.
"""
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import os

def create_certificate():
    """
    Dino Gıda için self-signed dijital imza sertifikası oluştur
    """
    print("=" * 60)
    print("SELF-SIGNED DİJİTAL İMZA SERTİFİKASI OLUŞTURULUYOR")
    print("=" * 60)
    
    # 1. Özel anahtar (Private Key) oluştur
    print("\n[1/5] Özel anahtar oluşturuluyor...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    print("[OK] Ozel anahtar olusturuldu (2048-bit RSA)")
    
    # 2. Sertifika bilgilerini hazırla
    print("\n[2/5] Sertifika bilgileri hazırlanıyor...")
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "TR"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "İzmir"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Menderes"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Dino Gıda San. Tic. Ltd. Şti."),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "E-Mutabakat Sistemi"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Dino Gıda Dijital İmza"),
        x509.NameAttribute(NameOID.EMAIL_ADDRESS, "info@dinogida.com.tr"),
    ])
    print("[OK] Sertifika bilgileri hazirlandi")
    
    # 3. Sertifika oluştur
    print("\n[3/5] Sertifika oluşturuluyor...")
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        # Sertifika 10 yıl geçerli
        datetime.utcnow() + timedelta(days=3650)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("dinogida.com.tr"),
            x509.DNSName("www.dinogida.com.tr"),
            x509.RFC822Name("info@dinogida.com.tr"),
        ]),
        critical=False,
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=0),
        critical=True,
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=True,  # Non-repudiation
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=True,
            crl_sign=True,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    ).sign(private_key, hashes.SHA256())
    print("[OK] Sertifika olusturuldu")
    
    # 4. Sertifikaları kaydet
    print("\n[4/5] Sertifikalar kaydediliyor...")
    
    # Sertifika klasörü oluştur
    cert_dir = "certificates"
    os.makedirs(cert_dir, exist_ok=True)
    
    # Özel anahtarı kaydet (şifreli)
    with open(f"{cert_dir}/dino_gida_private.key", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    print(f"[OK] Ozel anahtar kaydedildi: {cert_dir}/dino_gida_private.key")
    
    # Sertifikayı kaydet (PEM formatı)
    with open(f"{cert_dir}/dino_gida_cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print(f"[OK] Sertifika kaydedildi: {cert_dir}/dino_gida_cert.pem")
    
    # PKCS#12 formatında kaydet (pyHanko için)
    from cryptography.hazmat.primitives.serialization import pkcs12
    
    pkcs12_data = pkcs12.serialize_key_and_certificates(
        name=b"Dino Gida Digital Signature",
        key=private_key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    with open(f"{cert_dir}/dino_gida.p12", "wb") as f:
        f.write(pkcs12_data)
    print(f"[OK] PKCS#12 sertifika kaydedildi: {cert_dir}/dino_gida.p12")
    
    # 5. Özet bilgileri göster
    print("\n[5/5] Sertifika özeti:")
    print("=" * 60)
    print(f"Konu (Subject): {cert.subject.rfc4514_string()}")
    print(f"Seri No: {cert.serial_number}")
    print(f"Geçerlilik: {cert.not_valid_before_utc} - {cert.not_valid_after_utc}")
    print(f"İmza Algoritması: SHA-256")
    print("=" * 60)
    
    print("\n[OK] BASARILI! Dijital imza sertifikasi olusturuldu.")
    print("\n[!] ONEMLI NOTLAR:")
    print("1. Bu bir SELF-SIGNED (kendi imzali) sertifikadir")
    print("2. Resmi kullanim icin E-Tugra veya Kamu SM'den sertifika alin")
    print("3. Ozel anahtar dosyasini GUVENLI bir yerde saklayin")
    print("4. Ozel anahtari asla paylaşmayin!")
    
    return True

if __name__ == "__main__":
    try:
        create_certificate()
    except Exception as e:
        print(f"\n[HATA] {e}")
        import traceback
        traceback.print_exc()

