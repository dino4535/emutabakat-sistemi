"""
Şirket sertifika yolu ve şifrelerini günceller.

Varsayılanlar:
- Dino (VKN: 4640067727) -> certificates/dino_gida.p12, parola: D!no-2025_Sign
- Bermer (VKN: 1660290656) -> certificates/bermer.p12, parola: B3rm3r-2025_Sign
"""
from backend.database import SessionLocal
from backend.models import Company


def main() -> None:
    db = SessionLocal()

    updates = [
        ("4640067727", "certificates/dino_gida.p12", "D!no-2025_Sign"),
        ("1660290656", "certificates/bermer.p12", "B3rm3r-2025_Sign"),
    ]

    for vkn, path, pwd in updates:
        company = db.query(Company).filter(Company.vkn == vkn).first()
        if not company:
            print(f"[DB] Şirket bulunamadı (VKN={vkn})")
            continue
        company.certificate_path = path
        company.certificate_password = pwd
        db.add(company)
        print(f"[DB] Güncellendi: {company.company_name} -> {path}")

    db.commit()
    db.close()
    print("[DB] Tamamlandı")


if __name__ == "__main__":
    main()


