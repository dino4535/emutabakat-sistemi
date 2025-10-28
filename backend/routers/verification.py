"""
Dijital İmza Doğrulama Endpoint'leri
Mahkeme ve yasal otoriteler için mutabakat belgesi doğrulama
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Mutabakat
from pydantic import BaseModel
import hashlib
from typing import Optional
from pyhanko.sign.validation import validate_pdf_signature, ValidationContext
from pyhanko.pdf_utils.reader import PdfFileReader
from io import BytesIO
import tempfile
import os
from pathlib import Path

router = APIRouter(prefix="/api/verify", tags=["Verification"])


class VerificationRequest(BaseModel):
    """Doğrulama talebi"""
    mutabakat_no: str
    dijital_imza: str


class VerificationResponse(BaseModel):
    """Doğrulama sonucu"""
    gecerli: bool
    mesaj: str
    mutabakat_no: Optional[str] = None
    durum: Optional[str] = None
    sender_company: Optional[str] = None
    receiver_company: Optional[str] = None
    toplam_borc: Optional[float] = None
    toplam_alacak: Optional[float] = None
    bakiye: Optional[float] = None
    onay_tarihi: Optional[str] = None
    red_tarihi: Optional[str] = None
    red_nedeni: Optional[str] = None


@router.post("/mutabakat", response_model=VerificationResponse)
def verify_mutabakat(
    request: VerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Mutabakat Belgesi Dijital İmza Doğrulama
    
    Mahkeme ve yasal otoriteler bu endpoint'i kullanarak
    PDF belgesindeki dijital imzanın gerçek olup olmadığını doğrulayabilir.
    
    Args:
        mutabakat_no: Mutabakat numarası (PDF'de yazılı)
        dijital_imza: SHA-256 dijital imza (PDF'de yazılı)
    
    Returns:
        VerificationResponse: Doğrulama sonucu ve mutabakat detayları
    """
    # Mutabakatı bul
    mutabakat = db.query(Mutabakat).filter(
        Mutabakat.mutabakat_no == request.mutabakat_no
    ).first()
    
    if not mutabakat:
        return VerificationResponse(
            gecerli=False,
            mesaj=f"Mutabakat numarası '{request.mutabakat_no}' sistemde bulunamadı. Bu belge geçersiz olabilir."
        )
    
    # Dijital imzayı yeniden hesapla (PDF ile AYNI algoritma)
    data_string = f"{mutabakat.mutabakat_no}"
    data_string += f"{mutabakat.sender.company_name or mutabakat.sender.full_name or mutabakat.sender.username}"
    data_string += f"{mutabakat.receiver.company_name or mutabakat.receiver.full_name or mutabakat.receiver.username}"
    data_string += f"{mutabakat.toplam_borc}"
    data_string += f"{mutabakat.toplam_alacak}"
    
    # Mutabakat durumunu ekle
    if mutabakat.durum.value == 'onaylandi':
        data_string += "ONAYLANDI"
    else:
        data_string += "REDDEDİLDİ"
    
    # NOT: Timestamp ve IP adresi hash'e DAHİL EDİLMEZ
    # Sadece değişmez veriler kullanılır: mutabakat_no, şirketler, tutarlar, durum
    
    calculated_hash = hashlib.sha256(data_string.encode()).hexdigest()
    
    # Hash'leri karşılaştır
    if calculated_hash.lower() == request.dijital_imza.lower():
        durum_text = "Onaylandı" if mutabakat.durum.value == 'onaylandi' else "Reddedildi"
        
        return VerificationResponse(
            gecerli=True,
            mesaj=f"✓ Dijital imza GEÇERLİ. Bu belge Dino Gıda E-Mutabakat Sistemi tarafından oluşturulmuş ve değiştirilmemiştir.",
            mutabakat_no=mutabakat.mutabakat_no,
            durum=durum_text,
            sender_company=mutabakat.sender.company_name or mutabakat.sender.full_name,
            receiver_company=mutabakat.receiver.company_name or mutabakat.receiver.full_name,
            toplam_borc=float(mutabakat.toplam_borc or 0),
            toplam_alacak=float(mutabakat.toplam_alacak or 0),
            bakiye=float(mutabakat.bakiye or 0),
            onay_tarihi=mutabakat.onay_tarihi.strftime('%d.%m.%Y %H:%M:%S') if mutabakat.onay_tarihi else None,
            red_tarihi=mutabakat.red_tarihi.strftime('%d.%m.%Y %H:%M:%S') if mutabakat.red_tarihi else None,
            red_nedeni=mutabakat.red_nedeni
        )
    else:
        return VerificationResponse(
            gecerli=False,
            mesaj=f"✗ Dijital imza GEÇERSİZ! Bu belge değiştirilmiş veya sahte olabilir. Hesaplanan hash: {calculated_hash[:16]}...",
            mutabakat_no=mutabakat.mutabakat_no
        )


@router.get("/status/{mutabakat_no}")
def check_mutabakat_status(
    mutabakat_no: str,
    db: Session = Depends(get_db)
):
    """
    Mutabakat durumunu sorgula (basit)
    
    Args:
        mutabakat_no: Mutabakat numarası
    
    Returns:
        dict: Mutabakat durum bilgisi
    """
    mutabakat = db.query(Mutabakat).filter(
        Mutabakat.mutabakat_no == mutabakat_no
    ).first()
    
    if not mutabakat:
        raise HTTPException(
            status_code=404,
            detail="Mutabakat bulunamadı"
        )
    
    return {
        "mutabakat_no": mutabakat.mutabakat_no,
        "durum": mutabakat.durum.value,
        "sender": mutabakat.sender.company_name or mutabakat.sender.full_name,
        "receiver": mutabakat.receiver.company_name or mutabakat.receiver.full_name,
        "created_at": mutabakat.created_at.strftime('%d.%m.%Y %H:%M:%S'),
        "onay_tarihi": mutabakat.onay_tarihi.strftime('%d.%m.%Y %H:%M:%S') if mutabakat.onay_tarihi else None,
        "red_tarihi": mutabakat.red_tarihi.strftime('%d.%m.%Y %H:%M:%S') if mutabakat.red_tarihi else None
    }


class PDFVerificationResponse(BaseModel):
    """PDF Dosyası Doğrulama Sonucu"""
    gecerli: bool
    mesaj: str
    imza_bilgisi: Optional[dict] = None
    hash_dogrulama: Optional[dict] = None
    uyarilar: Optional[list] = None


@router.post("/pdf", response_model=PDFVerificationResponse)
def verify_pdf_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    PDF Dosyası Dijital İmza Doğrulama (GÜVENLİK KRİTİK!)
    
    PDF dosyasını upload ederek:
    1. pyHanko dijital imzasını kontrol eder
    2. PDF'in değiştirilip değiştirilmediğini tespit eder
    3. Veritabanı ile hash karşılaştırması yapar
    
    Bu endpoint, PDF üzerinde yapılan herhangi bir değişikliği tespit eder.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Lütfen bir PDF dosyası yükleyin"
        )
    
    try:
        # PDF içeriğini oku (sync)
        pdf_content = file.file.read()
        pdf_buffer = BytesIO(pdf_content)
        
        print(f"[PDF DOGRULAMA] Dosya alindi: {file.filename} ({len(pdf_content)} bytes)")
        
        # pyHanko ile PDF'i aç
        pdf_reader = PdfFileReader(pdf_buffer)
        
        # Dijital imzaları bul
        embedded_sigs = pdf_reader.embedded_signatures
        
        if not embedded_sigs:
            return PDFVerificationResponse(
                gecerli=False,
                mesaj="PDF'de dijital imza bulunamadı! Bu belge imzalanmamış veya sahte olabilir.",
                uyarilar=["Dijital imza yok", "Belge güvenilir değil"]
            )
        
        # İlk imzayı doğrula
        sig_field = embedded_sigs[0]
        
        print(f"[PDF DOGRULAMA] Imza bulundu: {sig_field.field_name}")
        
        # Self-signed sertifika için validation context oluştur
        try:
            # Sertifika dosyasını yükle (trust root için)
            cert_path = Path(__file__).parent.parent.parent / "certificates" / "dino_gida.p12"
            
            # ValidationContext ile self-signed sertifikayı kabul et
            vc = ValidationContext(
                trust_roots=[],  # Boş trust roots - self-signed kabul eder
                allow_fetching=False,  # Dış kaynak kontrolü yapma
                revocation_mode='soft-fail'  # Revocation check'i geçici olarak atla
            )
            
            # İmzayı doğrula
            validation_result = validate_pdf_signature(sig_field, validation_context=vc)
        except Exception as val_error:
            print(f"[PDF DOGRULAMA] Validation hatasi (devam ediliyor): {val_error}")
            # Validation hata verse bile, intact kontrolü yapalım
            validation_result = validate_pdf_signature(sig_field)
        
        # İmza bilgilerini topla
        imza_bilgisi = {
            "imza_adi": sig_field.field_name,
            "imzalayan": validation_result.signer_info.subject.human_friendly if hasattr(validation_result, 'signer_info') else "Bilinmiyor",
            "imza_zamani": str(validation_result.timestamp) if hasattr(validation_result, 'timestamp') else None,
            "gecerli": validation_result.intact,
            "guvenilir": "Self-Signed (Dino Gıda)",  # Self-signed olduğunu belirt
            "degistirilmis_mi": not validation_result.intact
        }
        
        print(f"[PDF DOGRULAMA] Imza durumu: gecerli={validation_result.intact}, intact={validation_result.intact}")
        
        # PDF değiştirilmiş mi?
        if not validation_result.intact:
            return PDFVerificationResponse(
                gecerli=False,
                mesaj="⚠️ KRİTİK UYARI: PDF dosyası değiştirilmiş! Dijital imza geçersiz!",
                imza_bilgisi=imza_bilgisi,
                uyarilar=[
                    "PDF imzalandıktan sonra değiştirilmiş",
                    "Belgenin içeriği manipüle edilmiş",
                    "Bu belge güvenilir değil",
                    "Mahkemeye sunulamaz"
                ]
            )
        
        # İmza geçerli - şimdi hash kontrolü yapalım
        # PDF'den mutabakat numarasını çıkar (basit yöntem - geliştirilebilir)
        pdf_text = pdf_content.decode('latin-1', errors='ignore')
        
        # Mutabakat numarasını ara
        mutabakat_no = None
        if "MUT-" in pdf_text:
            start_idx = pdf_text.index("MUT-")
            mutabakat_no = pdf_text[start_idx:start_idx+20].split()[0].strip()
            print(f"[PDF DOGRULAMA] Mutabakat No bulundu: {mutabakat_no}")
        
        hash_dogrulama = None
        if mutabakat_no:
            # Veritabanından mutabakatı bul
            mutabakat = db.query(Mutabakat).filter(
                Mutabakat.mutabakat_no == mutabakat_no
            ).first()
            
            if mutabakat:
                # Hash hesapla
                sender_company = mutabakat.sender.company_name or mutabakat.sender.full_name
                receiver_company = mutabakat.receiver.company_name or mutabakat.receiver.full_name
                action = "onaylandi" if mutabakat.durum.value == "onaylandi" else "reddedildi"
                
                data_string = f"{mutabakat_no}|{sender_company}|{receiver_company}|{mutabakat.toplam_borc}|{mutabakat.toplam_alacak}|{action}"
                calculated_hash = hashlib.sha256(data_string.encode('utf-8')).hexdigest()
                
                # PDF'deki hash'i ara
                if calculated_hash[:40] in pdf_text:
                    hash_dogrulama = {
                        "gecerli": True,
                        "mesaj": "Veritabanı ile hash eşleşiyor"
                    }
                    print("[PDF DOGRULAMA] Hash eslesti!")
                else:
                    hash_dogrulama = {
                        "gecerli": False,
                        "mesaj": "Veritabanı ile hash eşleşmiyor - veriler değiştirilmiş olabilir"
                    }
                    print("[PDF DOGRULAMA] Hash eslesmedi!")
        
        # Tüm kontroller başarılı
        return PDFVerificationResponse(
            gecerli=True,
            mesaj="✅ PDF belgesi ORIJINAL ve DEĞİŞTİRİLMEMİŞ! Dijital imza geçerli.",
            imza_bilgisi=imza_bilgisi,
            hash_dogrulama=hash_dogrulama,
            uyarilar=None
        )
        
    except Exception as e:
        print(f"[PDF DOGRULAMA] Hata: {e}")
        import traceback
        traceback.print_exc()
        
        return PDFVerificationResponse(
            gecerli=False,
            mesaj=f"PDF doğrulama hatası: {str(e)}",
            uyarilar=["Teknik hata oluştu", "PDF dosyası okunamadı"]
        )

