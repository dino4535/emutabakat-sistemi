"""
Self-signed PKCS#12 (.p12) sertifikaları üretir ve certificates/ altına kaydeder.

Öntanımlı şirketler (müşteri bilgileri ve parolalarla):
- Dino Gıda -> dino_gida.p12 (parola: Dino2025!@)
- Bermer -> bermer.p12 (parola: Bermer2025!@)

Notlar:
- Önce Python cryptography ile üretmeyi dener; yoksa openssl komutuna düşer.
- Üretilen p12'ler git'e eklenmemelidir; sadece sunucuda kullanılmak içindir.
"""
import os
import sys
import subprocess
from pathlib import Path


COMPANIES = [
    {
        "name": "Dino Gıda San. Tic. Ltd. Şti.",
        "cn": "DINO GIDA",
        "outfile": "dino_gida.p12",
        "password": "Dino2025!@",
        "email": "info@dinogida.com.tr",
        "phone": "+908502204566",
        "address": "Görece Cumhuriyet Mah. Gülçırpı Cad. No:19 Menderes/İZMİR",
        "owners": ["Hüseyin Kaplan", "İbrahim Kaplan"],
    },
    {
        "name": "BERMER ALKOLLÜ İÇKİLER MEŞRUBAT PAZARLAMA DAĞITIM SANAYİ TİCARET LİMİTED ŞİRKETİ",
        "cn": "BERMER",
        "outfile": "bermer.p12",
        "password": "Bermer2025!@",
        "email": "info@bermer.com.tr",
        "phone": "+908502204566",
        "address": "Görece Cumhuriyet Mah. Gülçırpı Cad. No:19 Menderes/İZMİR",
        "owners": [],
    },
]


def ensure_cert_dir() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    cert_dir = project_root / "certificates"
    cert_dir.mkdir(parents=True, exist_ok=True)
    return cert_dir


def openssl_exists() -> bool:
    try:
        subprocess.run(["openssl", "version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def generate_with_openssl(common_name: str, company_name: str, p12_path: Path, password: str, email: str | None = None) -> None:
    tmp_key = p12_path.with_suffix(".key")
    tmp_crt = p12_path.with_suffix(".crt")

    # Key + self-signed cert
    subj = f"/C=TR/ST=Istanbul/L=Istanbul/O={company_name}/OU=IT/CN={common_name}"
    if email:
        subj += f"/emailAddress={email}"
    subprocess.run([
        "openssl", "req", "-newkey", "rsa:2048", "-nodes",
        "-keyout", str(tmp_key),
        "-x509", "-days", "3650",
        "-out", str(tmp_crt),
        "-subj", subj
    ], check=True)

    # Package to PKCS#12
    subprocess.run([
        "openssl", "pkcs12", "-export",
        "-inkey", str(tmp_key),
        "-in", str(tmp_crt),
        "-name", f"{company_name} Sign",
        "-out", str(p12_path),
        "-passout", f"pass:{password}"
    ], check=True)

    # Cleanup temp
    try:
        tmp_key.unlink(missing_ok=True)
        tmp_crt.unlink(missing_ok=True)
    except Exception:
        pass


def generate_with_cryptography(common_name: str, company_name: str, p12_path: Path, password: str, email: str | None = None) -> None:
    from datetime import datetime, timedelta
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    try:
        from cryptography.hazmat.primitives.serialization import pkcs12
    except Exception:
        # Eski sürümlerde pkcs12 modülü olmayabilir
        raise RuntimeError("cryptography pkcs12 desteği bulunamadı")

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "TR"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Istanbul"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Istanbul"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, company_name),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "IT"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow() - timedelta(days=1))
        .not_valid_after(datetime.utcnow() + timedelta(days=3650))
    )
    # Email SAN ekle
    if email:
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.RFC822Name(email)]),
            critical=False,
        )
    cert = builder.sign(private_key=key, algorithm=hashes.SHA256())

    pfx = pkcs12.serialize_key_and_certificates(
        name=bytes(f"{company_name} Sign", "utf-8"),
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode("utf-8")),
    )

    with open(p12_path, "wb") as f:
        f.write(pfx)


def main() -> int:
    cert_dir = ensure_cert_dir()
    print(f"[CERT] Hedef dizin: {cert_dir}")

    can_use_openssl = openssl_exists()
    if not can_use_openssl:
        print("[CERT] openssl bulunamadı, cryptography ile üretmeyi deneyeceğim")

    for c in COMPANIES:
        p12_path = cert_dir / c["outfile"]
        if p12_path.exists():
            print(f"[CERT] Zaten var, atlanıyor: {p12_path.name}")
            continue

        try:
            if can_use_openssl:
                generate_with_openssl(common_name=c["cn"], company_name=c["name"], p12_path=p12_path, password=c["password"], email=c.get("email"))
            else:
                generate_with_cryptography(common_name=c["cn"], company_name=c["name"], p12_path=p12_path, password=c["password"], email=c.get("email"))
            print(f"[CERT] Olusturuldu: {p12_path.name}")
        except Exception as e:
            print(f"[CERT] Hata: {c['outfile']}: {e}")
            return 1

    print("[CERT] Tamamlandı")
    print("[CERT] Parolalar:")
    for c in COMPANIES:
        print(f" - {c['outfile']}: {c['password']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


