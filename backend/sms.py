"""
GoldSMS API Entegrasyonu
"""
import requests
import os
from typing import Optional
from backend.logger import logger
import urllib3

# SSL uyarılarını bastır
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GoldSMS:
    """GoldSMS API ile SMS gönderme (Multi-Company)"""
    
    def __init__(self, company=None):
        """
        Args:
            company: Company objesi (opsiyonel, Multi-Company için)
                     Eğer verilirse company'nin SMS ayarları kullanılır
                     Verilmezse env'den alınır (geriye dönük uyumluluk)
        """
        if company and company.sms_enabled:
            # Multi-Company: Şirketin kendi SMS ayarları
            self.username = company.sms_username or os.getenv("GOLDSMS_USERNAME", "dinogıda45")
            self.password = company.sms_password or os.getenv("GOLDSMS_PASSWORD", "Dino45??*123D")
            self.originator = company.sms_header or os.getenv("GOLDSMS_ORIGINATOR", "DiNO GIDA")
        else:
            # Fallback: Env'den al (geriye dönük uyumluluk)
            self.username = os.getenv("GOLDSMS_USERNAME", "dinogıda45")
            self.password = os.getenv("GOLDSMS_PASSWORD", "Dino45??*123D")
            self.originator = os.getenv("GOLDSMS_ORIGINATOR", "DiNO GIDA")
        
        # GoldSMS API v3 URL
        self.api_url = os.getenv("GOLDSMS_API_URL", "http://apiv3.goldmesaj.net/api/sendSMS")
        # Frontend URL (mutabakat detay linki için)
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    def format_phone(self, phone: str) -> Optional[str]:
        """
        Telefon numarasını formatla
        Örnek: +905551234567, 05551234567, 5551234567 -> 905551234567
        """
        if not phone:
            return None
        
        # Tüm boşlukları ve özel karakterleri temizle
        phone = ''.join(filter(str.isdigit, phone))
        
        # 0 ile başlıyorsa kaldır ve 90 ekle
        if phone.startswith('0'):
            phone = '90' + phone[1:]
        # 90 ile başlamıyorsa ekle
        elif not phone.startswith('90'):
            phone = '90' + phone
        
        # Türk telefon numarası kontrolü (90 + 10 rakam = 12 rakam)
        if len(phone) == 12 and phone.startswith('90'):
            return phone
        
        return None
    
    def check_credit(self) -> bool:
        """
        GoldSMS kredi kontrolü
        
        Returns:
            bool: Kredi varsa True
        """
        try:
            credit_url = "http://apiv3.goldmesaj.net/api/kredi/get"
            payload = {
                'username': self.username,
                'password': self.password
            }
            
            response = requests.post(
                credit_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'ok' and result.get('result', 0) > 1:
                    logger.info(f"GoldSMS kredi: {result.get('result')} SMS")
                    return True
                else:
                    logger.error(f"GoldSMS kredi yetersiz: {result}")
                    return False
            else:
                logger.error(f"GoldSMS kredi kontrol hatası: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"GoldSMS kredi kontrol hatası: {e}")
            return False
    
    def send_sms(self, phone: str, message: str) -> bool:
        """
        SMS gönder
        
        Args:
            phone: Telefon numarası (örn: +905551234567)
            message: Mesaj içeriği
            
        Returns:
            bool: Başarılı ise True
        """
        try:
            # Önce kredi kontrolü yap
            if not self.check_credit():
                logger.error("GoldSMS kredisi yetersiz veya erişilemiyor")
                return False
            
            # Telefon numarasını formatla
            formatted_phone = self.format_phone(phone)
            
            if not formatted_phone:
                logger.error(f"Geçersiz telefon numarası: {phone}")
                return False
            
            # GoldSMS API v3 parametreleri - Doğru format
            # username/password root seviyede, message objesi içinde sender/text/utf8/gsm
            payload_json = {
                'username': self.username,
                'password': self.password,
                'sdate': '',  # Boş = hemen gönder
                'vperiod': '23',  # 23 saat boyunca gönderilmeye çalışılacak
                'gate': 0,  # Sabit değer
                'message': {
                    'sender': self.originator,  # SMS başlığı
                    'text': message,  # SMS metni
                    'utf8': '1',  # Türkçe karakter desteği
                    'gsm': [formatted_phone]  # Telefon numaraları array içinde
                }
            }
            
            # API isteği
            logger.info(f"SMS gönderiliyor: {formatted_phone}")
            
            response = requests.post(
                self.api_url,
                json=payload_json,
                headers={'Content-Type': 'application/json'},
                timeout=60,  # Timeout 60 saniyeye çıkarıldı
                verify=False  # SSL doğrulama kapalı
            )
            
            # Yanıt kontrolü
            logger.debug(f"SMS API Yanıt - Status: {response.status_code}, Content: {response.text}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.debug(f"SMS API Response: {result}")
                    
                    # GoldSMS v3 başarı kontrolü (Türkçe yanıt formatı)
                    # sonuc: true/false
                    # mesaj: hata mesajı
                    # gonderilenAdet: gönderilen SMS adedi
                    if result.get('sonuc') == True:
                        sent_count = result.get('gonderilenAdet', 0)
                        message_id = result.get('result', {}).get('messageid', 'N/A')
                        logger.info(f"SMS başarıyla gönderildi: {formatted_phone}, Adet: {sent_count}, ID: {message_id}")
                        return True
                    else:
                        error_msg = result.get('mesaj', 'Bilinmeyen hata')
                        error_status = result.get('status', 'N/A')
                        logger.error(f"SMS gönderimi başarısız: Status={error_status}, Mesaj={error_msg}")
                        return False
                except Exception as e:
                    logger.error(f"SMS yanıt parse hatası: {e}, Raw: {response.text}")
                    return False
            else:
                logger.error(f"SMS API hatası: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("SMS API zaman aşımı")
            return False
        except Exception as e:
            logger.error(f"SMS gönderme hatası: {e}")
            return False
    
    def send_mutabakat_notification(
        self, 
        phone: str, 
        customer_name: str, 
        mutabakat_no: str,
        amount: float,
        approval_token: str = None
    ) -> bool:
        """
        Mutabakat bildirimi SMS'i gönder
        
        Args:
            phone: Müşteri telefon numarası
            customer_name: Müşteri adı
            mutabakat_no: Mutabakat numarası
            amount: Toplam tutar
            approval_token: Onay token'ı (tek kullanımlık link için)
            
        Returns:
            bool: Başarılı ise True
        """
        # Tutarı formatla
        formatted_amount = f"{amount:,.2f} TL"
        
        # Tek kullanımlık onay linki
        if approval_token:
            from backend.utils.tokens import get_approval_link
            approval_link = get_approval_link(approval_token)
        else:
            approval_link = "Sisteme giris yaparak"
        
        # SMS mesajı (tek kullanımlık link ile)
        message = (
            f"Sayin {customer_name},\n"
            f"Mutabakat No: {mutabakat_no}\n"
            f"Tutar: {formatted_amount}\n"
            f"Onaylamak icin:\n"
            f"{approval_link}\n"
            f"- DiNO GIDA"
        )
        
        return self.send_sms(phone, message)
    
    def send_mutabakat_approved(
        self,
        phone: str,
        customer_name: str,
        mutabakat_no: str
    ) -> bool:
        """
        Mutabakat onay bildirimi SMS'i gönder
        
        Args:
            phone: Firma telefon numarası
            customer_name: Müşteri adı
            mutabakat_no: Mutabakat numarası
            
        Returns:
            bool: Başarılı ise True
        """
        message = (
            f"Mutabakat onaylandi!\n"
            f"Musteri: {customer_name}\n"
            f"Mutabakat No: {mutabakat_no}\n"
            f"- DiNO GIDA"
        )
        
        return self.send_sms(phone, message)
    
    def send_mutabakat_rejected(
        self,
        phone: str,
        customer_name: str,
        mutabakat_no: str,
        reason: str
    ) -> bool:
        """
        Mutabakat red bildirimi SMS'i gönder
        
        Args:
            phone: Firma telefon numarası
            customer_name: Müşteri adı
            mutabakat_no: Mutabakat numarası
            reason: Red nedeni
            
        Returns:
            bool: Başarılı ise True
        """
        message = (
            f"Mutabakat reddedildi!\n"
            f"Musteri: {customer_name}\n"
            f"Mutabakat No: {mutabakat_no}\n"
            f"Neden: {reason[:50]}\n"
            f"- DiNO GIDA"
        )
        
        return self.send_sms(phone, message)


# Global SMS instance
sms_service = GoldSMS()

