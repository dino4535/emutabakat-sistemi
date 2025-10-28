# -*- coding: utf-8 -*-
"""
Email Bildirim Servisi
Mutabakat sonuçları için detaylı email gönderimi
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
import os


class EmailService:
    """Email gönderim servisi"""
    
    def __init__(self):
        """
        Email servis ayarlarını yükle (.env'den)
        
        Gerekli .env değişkenleri:
        - SMTP_HOST: SMTP sunucu adresi (örn: smtp.gmail.com)
        - SMTP_PORT: SMTP port (örn: 587)
        - SMTP_USER: SMTP kullanıcı adı
        - SMTP_PASSWORD: SMTP şifresi
        - SMTP_FROM_EMAIL: Gönderen email adresi
        - SMTP_FROM_NAME: Gönderen adı
        """
        self.smtp_host = os.getenv('SMTP_HOST')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('SMTP_FROM_EMAIL')
        self.from_name = os.getenv('SMTP_FROM_NAME', 'E-Mutabakat Sistemi')
        
        self.enabled = all([
            self.smtp_host,
            self.smtp_user,
            self.smtp_password,
            self.from_email
        ])
        
        if not self.enabled:
            print("[EMAIL] SMTP ayarları eksik, email gönderimi devre dışı")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Email gönder
        
        Args:
            to_email: Alıcı email adresi
            subject: Email konusu
            html_body: HTML içerik
            text_body: Plain text içerik (opsiyonel)
        
        Returns:
            bool: Başarılı ise True
        """
        if not self.enabled:
            print(f"[EMAIL] Servis devre dışı, email gönderilemedi: {to_email}")
            return False
        
        try:
            # Email mesajı oluştur
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Text ve HTML kısımları ekle
            if text_body:
                part1 = MIMEText(text_body, 'plain', 'utf-8')
                msg.attach(part1)
            
            part2 = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(part2)
            
            # SMTP ile gönder
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"[EMAIL] Email başarıyla gönderildi: {to_email}")
            return True
            
        except Exception as e:
            print(f"[EMAIL] Email gönderme hatası: {e}")
            return False
    
    def send_mutabakat_approved(
        self,
        to_email: str,
        company_name: str,
        customer_name: str,
        mutabakat_no: str,
        donem_baslangic: datetime,
        donem_bitis: datetime,
        toplam_borc: float,
        toplam_alacak: float,
        bakiye: float,
        onay_tarihi: datetime
    ) -> bool:
        """
        Mutabakat onaylandı bildirimi gönder
        """
        subject = f"✅ Mutabakat Onaylandı - {mutabakat_no}"
        
        # HTML email template
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .info-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        .info-table th {{ background: #4CAF50; color: white; padding: 10px; text-align: left; }}
        .info-table td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        .amount {{ font-size: 18px; font-weight: bold; color: #4CAF50; }}
        .footer {{ text-align: center; padding: 15px; color: #777; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Mutabakat Onaylandı</h1>
        </div>
        <div class="content">
            <p>Sayın <strong>{company_name}</strong>,</p>
            
            <p><strong>{customer_name}</strong> firması mutabakatınızı onaylamıştır.</p>
            
            <table class="info-table">
                <tr>
                    <th colspan="2">Mutabakat Bilgileri</th>
                </tr>
                <tr>
                    <td><strong>Mutabakat No:</strong></td>
                    <td>{mutabakat_no}</td>
                </tr>
                <tr>
                    <td><strong>Dönem:</strong></td>
                    <td>{donem_baslangic.strftime('%d.%m.%Y')} - {donem_bitis.strftime('%d.%m.%Y')}</td>
                </tr>
                <tr>
                    <td><strong>Onay Tarihi:</strong></td>
                    <td>{onay_tarihi.strftime('%d.%m.%Y %H:%M')}</td>
                </tr>
            </table>
            
            <table class="info-table">
                <tr>
                    <th colspan="2">Finansal Bilgiler</th>
                </tr>
                <tr>
                    <td><strong>Toplam Borç:</strong></td>
                    <td class="amount">{toplam_borc:,.2f} TL</td>
                </tr>
                <tr>
                    <td><strong>Toplam Alacak:</strong></td>
                    <td class="amount">{toplam_alacak:,.2f} TL</td>
                </tr>
                <tr>
                    <td><strong>Bakiye:</strong></td>
                    <td class="amount">{bakiye:,.2f} TL</td>
                </tr>
            </table>
            
            <p>Dijital imzalı mutabakat belgesini sistemden indirebilirsiniz.</p>
        </div>
        <div class="footer">
            <p>Bu email otomatik olarak oluşturulmuştur.</p>
            <p>© 2025 E-Mutabakat Sistemi</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(to_email, subject, html_body)
    
    def send_mutabakat_rejected(
        self,
        to_email: str,
        company_name: str,
        customer_name: str,
        mutabakat_no: str,
        donem_baslangic: datetime,
        donem_bitis: datetime,
        toplam_borc: float,
        toplam_alacak: float,
        bakiye: float,
        red_nedeni: str,
        red_tarihi: datetime
    ) -> bool:
        """
        Mutabakat reddedildi bildirimi gönder
        """
        subject = f"❌ Mutabakat Reddedildi - {mutabakat_no}"
        
        # HTML email template
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #f44336; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .info-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        .info-table th {{ background: #f44336; color: white; padding: 10px; text-align: left; }}
        .info-table td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        .reason-box {{ background: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 5px; }}
        .amount {{ font-size: 18px; font-weight: bold; color: #f44336; }}
        .footer {{ text-align: center; padding: 15px; color: #777; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>❌ Mutabakat Reddedildi</h1>
        </div>
        <div class="content">
            <p>Sayın <strong>{company_name}</strong>,</p>
            
            <p><strong>{customer_name}</strong> firması mutabakatınızı reddetmiştir.</p>
            
            <div class="reason-box">
                <strong>Red Nedeni:</strong><br>
                {red_nedeni}
            </div>
            
            <table class="info-table">
                <tr>
                    <th colspan="2">Mutabakat Bilgileri</th>
                </tr>
                <tr>
                    <td><strong>Mutabakat No:</strong></td>
                    <td>{mutabakat_no}</td>
                </tr>
                <tr>
                    <td><strong>Dönem:</strong></td>
                    <td>{donem_baslangic.strftime('%d.%m.%Y')} - {donem_bitis.strftime('%d.%m.%Y')}</td>
                </tr>
                <tr>
                    <td><strong>Red Tarihi:</strong></td>
                    <td>{red_tarihi.strftime('%d.%m.%Y %H:%M')}</td>
                </tr>
            </table>
            
            <table class="info-table">
                <tr>
                    <th colspan="2">Finansal Bilgiler</th>
                </tr>
                <tr>
                    <td><strong>Toplam Borç:</strong></td>
                    <td class="amount">{toplam_borc:,.2f} TL</td>
                </tr>
                <tr>
                    <td><strong>Toplam Alacak:</strong></td>
                    <td class="amount">{toplam_alacak:,.2f} TL</td>
                </tr>
                <tr>
                    <td><strong>Bakiye:</strong></td>
                    <td class="amount">{bakiye:,.2f} TL</td>
                </tr>
            </table>
            
            <p>Lütfen müşterinizle iletişime geçip konuyu netleştiriniz.</p>
        </div>
        <div class="footer">
            <p>Bu email otomatik olarak oluşturulmuştur.</p>
            <p>© 2025 E-Mutabakat Sistemi</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(to_email, subject, html_body)


# Singleton instance
email_service = EmailService()

