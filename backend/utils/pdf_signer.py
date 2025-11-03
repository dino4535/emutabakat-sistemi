"""
PDF Dijital İmza Servisi
pyHanko kullanarak PDF'lere dijital imza ekler (Multi-Company)
"""
from pyhanko.sign import signers
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko import stamp
from pyhanko.sign import fields
from pyhanko.sign.fields import MDPPerm
from pyhanko.sign.general import SigningError
from datetime import datetime
import os
from pathlib import Path
import traceback
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

class PDFSigner:
    """PDF dijital imza yöneticisi (Multi-Company)"""
    
    def __init__(self):
        """Proje dizinini ayarla"""
        # Proje root dizinini bul
        current_file = Path(__file__)  # pdf_signer.py
        backend_dir = current_file.parent.parent  # backend/
        self.project_root = backend_dir.parent  # Proje1/
        self.cert_dir = self.project_root / "certificates"
        
        # Şirket bazlı signer cache
        self._signer_cache = {}
        
        print(f"[DIJITAL IMZA] Sertifika dizini: {self.cert_dir}")
    
    def _load_certificate(self, cert_path: str, cert_password: Optional[str] = None):
        """
        Belirli bir sertifikayı yükle
        
        Args:
            cert_path: Sertifika dosyası yolu (örn: certificates/bermer.p12)
            cert_password: Sertifika şifresi (None = şifresiz)
        
        Returns:
            SimpleSigner instance veya None
        """
        # Cache key oluştur
        cache_key = f"{cert_path}:{cert_password}"
        
        # Cache'de varsa döndür
        if cache_key in self._signer_cache:
            return self._signer_cache[cache_key]
        
        # Yol normalizasyonu: ters eğik çizgileri düzelt, sadece dosya adı ise 'certificates/' öne ekle
        norm_path_str = (cert_path or "").replace("\\", "/").strip()
        if not norm_path_str:
            print("[DIJITAL IMZA] Sertifika yolu bos")
            return None
        # Absolute değilse ve 'certificates/' ile başlamıyorsa öne ekle
        if not Path(norm_path_str).is_absolute() and not norm_path_str.startswith("certificates/"):
            norm_path_str = f"certificates/{norm_path_str}"

        # Tam yol oluştur
        full_path = self.project_root / norm_path_str if not Path(norm_path_str).is_absolute() else Path(norm_path_str)

        # Eğer verilen yol yoksa, aynı dosyayı cert_dir altında aramayı dene (ek güvenlik)
        if not full_path.exists():
            candidate = self.cert_dir / Path(norm_path_str).name
            if candidate.exists():
                full_path = candidate
        
        if not full_path.exists():
            print(f"[DIJITAL IMZA] Sertifika bulunamadi: {full_path}")
            return None
        
        try:
            # PKCS#12 sertifikasını yükle
            # Parolayı sanitize et: trim + Unicode normalize (DB'den gelen boşluk/karakter sorunlarını önle)
            passphrase = None
            if cert_password:
                import unicodedata
                sanitized = unicodedata.normalize("NFC", cert_password.strip())
                passphrase = sanitized.encode()
            
            signer = signers.SimpleSigner.load_pkcs12(
                pfx_file=str(full_path),
                passphrase=passphrase
            )
            
            # Cache'e kaydet
            self._signer_cache[cache_key] = signer
            
            print(f"[DIJITAL IMZA] [OK] Sertifika yuklendi: {full_path.name}")
            return signer
            
        except Exception as e:
            print(f"[DIJITAL IMZA] [!] Sertifika yuklenemedi ({full_path.name}): {e}")
            traceback.print_exc()
            return None
    
    def _sign_pdf_sync(
        self,
        input_pdf_path: str,
        output_pdf_path: str,
        company_name: str,
        signer
    ) -> str:
        """
        PDF'e dijital imza ekle (senkron - thread'de çalışacak)
        """
        try:
            # PDF'i aç
            with open(input_pdf_path, 'rb') as inf:
                w = IncrementalPdfFileWriter(inf)
                
                # İmza alanı metadata'sı (GÜVENLİK: Değişiklik yapılamaz!)
                meta = signers.PdfSignatureMetadata(
                    field_name='CompanySignature',
                    name=company_name,
                    location='Türkiye',
                    reason='E-Mutabakat Belgesi Dijital İmzası',
                    docmdp_permissions=MDPPerm.NO_CHANGES
                )
                
                # İmzayı ekle (görünümsüz - sadece PDF özelliklerinde)
                out = signers.sign_pdf(
                    w,
                    signature_meta=meta,
                    signer=signer,
                    existing_fields_only=False
                )
            
            # İmzalı PDF'i kaydet
            with open(output_pdf_path, 'wb') as outf:
                outf.write(out.getbuffer())
            
            return output_pdf_path
            
        except Exception as e:
            raise e
    
    def sign_pdf(
        self, 
        input_pdf_path: str, 
        output_pdf_path: str = None,
        company_name: str = "Dino Gıda San. Tic. Ltd. Şti.",
        cert_path: str = "certificates/dino_gida.p12",
        cert_password: Optional[str] = None
    ) -> str:
        """
        PDF'e dijital imza ekle (Multi-Company)
        
        Args:
            input_pdf_path: İmzalanacak PDF dosyası yolu
            output_pdf_path: İmzalı PDF'in kaydedileceği yer (opsiyonel)
            company_name: Şirket adı (imza metadata'sında kullanılacak)
            cert_path: Sertifika dosyası yolu
            cert_password: Sertifika şifresi
        
        Returns:
            İmzalı PDF dosyası yolu
        """
        # Sertifikayı yükle
        signer = self._load_certificate(cert_path, cert_password)
        
        if not signer:
            print("[DIJITAL IMZA] Sertifika yuklu degil, imza atlanildi")
            return input_pdf_path
        
        if output_pdf_path is None:
            # Aynı dosyanın üzerine yaz
            output_pdf_path = input_pdf_path
        
        try:
            print(f"[DIJITAL IMZA] PDF imzalaniyor: {input_pdf_path} ({company_name})")
            
            # ThreadPoolExecutor ile başka bir thread'de çalıştır
            # Bu sayede mevcut event loop'u bloklamadan asyncio.run() çağrısı yapabiliriz
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self._sign_pdf_sync,
                    input_pdf_path,
                    output_pdf_path,
                    company_name,
                    signer
                )
                output_path = future.result(timeout=30)  # 30 saniye timeout
            
            print(f"[DIJITAL IMZA] [OK] PDF basariyla imzalandi: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"[DIJITAL IMZA] [!] Imzalama hatasi: {e}")
            traceback.print_exc()
            # Hata durumunda orijinal dosyayı döndür
            return input_pdf_path
    
    def is_ready(self, cert_path: str = "certificates/dino_gida.p12", cert_password: Optional[str] = None) -> bool:
        """
        Dijital imza sistemi hazır mı?
        
        Args:
            cert_path: Kontrol edilecek sertifika yolu
            cert_password: Sertifika şifresi
        """
        signer = self._load_certificate(cert_path, cert_password)
        return signer is not None


# Singleton instance
pdf_signer = PDFSigner()

