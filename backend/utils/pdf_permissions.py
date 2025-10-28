"""
PDF İzin Yönetimi
pikepdf kullanarak PDF'lere güvenlik ve izinler ekler
"""
import pikepdf
from pathlib import Path


def apply_pdf_permissions(pdf_path: str) -> str:
    """
    PDF'e izinler uygula
    
    İzin Verilen:
    - Yazdırma (Printing)
    - Dijital İmza Ekleme (Signing/Annotations)
    
    İzin Verilmeyen:
    - Belge Değiştirme (Modify)
    - Sayfa Ekleme/Çıkarma (Extract/Assemble)
    - İçerik Kopyalama (Copy/Extract Content)
    - Form Doldurma (Fill Forms)
    - Yorum Ekleme (Comment - imza hariç)
    
    Args:
        pdf_path: PDF dosyası yolu
        
    Returns:
        İşlenmiş PDF dosyası yolu
    """
    try:
        print(f"[PDF IZINLER] PDF'e izinler ekleniyor: {pdf_path}")
        
        # PDF'i aç
        with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
            
            # İzinler ayarla
            # Kullanıcı şifresi yok (PDF açılabilir)
            # Sahip şifresi var (izin düzenlemeleri korunur)
            permissions = pikepdf.Permissions(
                accessibility=True,          # Ekran okuyucu erişimi (engelli kullanıcılar için)
                extract=False,               # İçerik kopyalama ENGELLENDI
                modify_annotation=True,      # İmza ekleme İZİN VERİLDİ
                modify_assembly=False,       # Sayfa ekleme/çıkarma ENGELLENDI
                modify_form=False,           # Form doldurma ENGELLENDI  
                modify_other=False,          # Diğer değişiklikler ENGELLENDI
                print_lowres=True,           # Düşük çözünürlük yazdırma İZİN VERİLDİ
                print_highres=True           # Yüksek çözünürlük yazdırma İZİN VERİLDİ
            )
            
            # Şifreleme uygula (owner password ile)
            # Kullanıcı şifresi YOK - PDF direkt açılır
            # Owner password VAR - İzinler korunur
            pdf.save(
                pdf_path,
                encryption=pikepdf.Encryption(
                    owner="Dino_Gida_Mutabakat_2024_Secure_Document",  # Sahip şifresi (sistem içi)
                    user="",                                            # Kullanıcı şifresi YOK (herkes açabilir)
                    R=6,                                                # Şifreleme seviyesi (256-bit AES) - En Güçlü
                    allow=permissions
                )
            )
        
        print(f"[PDF IZINLER] [OK] Izinler basariyla uygulandi (256-bit AES)")
        print("  [+] Yazdirma: IZIN VERILDI")
        print("  [+] Dijital Imza: IZIN VERILDI")
        print("  [-] Icerik Kopyalama: ENGELLENDI")
        print("  [-] Sayfa Degistirme: ENGELLENDI")
        print("  [-] Form Doldurma: ENGELLENDI")
        print("  [-] Belge Duzenleme: ENGELLENDI")
        print("  [*] Sifreleme: 256-bit AES (R=6 - En Guclu)")
        
        return pdf_path
        
    except Exception as e:
        print(f"[PDF IZINLER] [!] Izin ekleme hatasi: {e}")
        # Hata olursa orijinal PDF'i dondur
        return pdf_path


def check_pdf_permissions(pdf_path: str) -> dict:
    """
    PDF izinlerini kontrol et
    
    Args:
        pdf_path: PDF dosyası yolu
        
    Returns:
        İzin bilgileri dict
    """
    try:
        with pikepdf.open(pdf_path) as pdf:
            if pdf.is_encrypted:
                perms = pdf.allow
                return {
                    "encrypted": True,
                    "accessibility": perms.accessibility,
                    "extract": perms.extract,
                    "modify_annotation": perms.modify_annotation,
                    "modify_assembly": perms.modify_assembly,
                    "modify_form": perms.modify_form,
                    "modify_other": perms.modify_other,
                    "print_lowres": perms.print_lowres,
                    "print_highres": perms.print_highres
                }
            else:
                return {"encrypted": False, "message": "PDF şifrelenmemiş"}
    except Exception as e:
        return {"error": str(e)}

