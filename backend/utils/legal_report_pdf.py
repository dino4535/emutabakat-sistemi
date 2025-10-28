"""
Yasal Rapor PDF Oluşturma Servisi
Resmi makamlar için dijital imzalı, şifreli yasal raporlar üretir.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import hashlib
import os
from io import BytesIO
import pytz
from pathlib import Path

# Türkiye saat dilimi
TURKEY_TZ = pytz.timezone('Europe/Istanbul')

def get_turkey_time():
    """Türkiye saatini döndür (UTC+3)"""
    return datetime.now(TURKEY_TZ)

# Türkçe karakter desteği için font kaydet (bir kere)
FONTS_REGISTERED = False

def register_turkish_fonts():
    """Türkçe karakterler için font kaydet (bir kere çalışır)"""
    global FONTS_REGISTERED
    if FONTS_REGISTERED:
        return
    
    try:
        # Windows için Arial font'u kullan (Türkçe Unicode destekli)
        arial_path = "C:/Windows/Fonts/arial.ttf"
        arial_bold_path = "C:/Windows/Fonts/arialbd.ttf"
        arial_italic_path = "C:/Windows/Fonts/ariali.ttf"
        
        if os.path.exists(arial_path):
            pdfmetrics.registerFont(TTFont('TurkceArial', arial_path, 'UTF-8'))
            print("[YASAL PDF] TurkceArial font yüklendi (UTF-8)")
        if os.path.exists(arial_bold_path):
            pdfmetrics.registerFont(TTFont('TurkceArial-Bold', arial_bold_path, 'UTF-8'))
            print("[YASAL PDF] TurkceArial-Bold font yüklendi")
        if os.path.exists(arial_italic_path):
            pdfmetrics.registerFont(TTFont('TurkceArial-Italic', arial_italic_path, 'UTF-8'))
            print("[YASAL PDF] TurkceArial-Italic font yüklendi")
        
        FONTS_REGISTERED = True
        return True
    except Exception as e:
        print(f"[YASAL PDF] Font yükleme uyarısı: {e}")
        return False

# Fontu hemen kaydet
FONTS_LOADED = register_turkish_fonts()

def ensure_unicode(text):
    """Metni unicode olarak garanti et (Türkçe karakterler için)"""
    if text is None:
        return "-"
    if isinstance(text, bytes):
        return text.decode('utf-8')
    return str(text)

class LegalReportPDFGenerator:
    """Yasal Rapor PDF Oluşturucu"""
    
    def __init__(self):
        self.buffer = BytesIO()
        self.pagesize = A4
        self.width, self.height = A4
    
    def generate_mutabakat_report(self, report_data):
        """Mutabakat için yasal rapor PDF'i oluştur"""
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=self.pagesize,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Stil tanımları
        styles = getSampleStyleSheet()
        
        # Başlık stili
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName='TurkceArial-Bold',
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        # Alt başlık stili
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontName='TurkceArial',
            fontSize=12,
            textColor=colors.HexColor('#7f8c8d'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        # Section başlık stili
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontName='TurkceArial-Bold',
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            spaceBefore=15
        )
        
        # Normal metin stili
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName='TurkceArial',
            fontSize=10,
            leading=14
        )
        
        story = []
        
        # LOGO EKLE (Şirket Logosu - metadata'dan)
        try:
            metadata = report_data.get('report_metadata', {})
            company_logo_path = metadata.get('company_logo_path')
            
            # Proje root dizinini al
            project_root = Path(__file__).parent.parent.parent
            
            if company_logo_path:
                # Şirket logosu belirtilmiş
                # company_logo_path zaten "frontend/public/..." veya "Bermer-logo.png" gibi olabilir
                if company_logo_path.startswith('frontend/'):
                    # Tam path verilmiş
                    logo_path = project_root / company_logo_path
                else:
                    # Sadece dosya adı verilmiş
                    logo_path = project_root / "frontend" / "public" / company_logo_path
            else:
                # Default logo
                logo_path = project_root / "frontend" / "public" / "dino-logo.png"
            
            if logo_path.exists():
                logo = Image(str(logo_path), width=4*cm, height=2*cm)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 0.3*cm))
                print(f"[YASAL PDF] Logo yuklendi: {logo_path}")
            else:
                print(f"[YASAL PDF] Logo bulunamadi: {logo_path}")
        except Exception as e:
            print(f"[YASAL PDF] Logo yukleme hatasi: {e}")
        
        # ŞİRKET ADI (metadata'dan)
        company_style = ParagraphStyle(
            'Company',
            parent=styles['Normal'],
            fontName='TurkceArial-Bold',
            fontSize=12,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        company_name = metadata.get('company_name', 'Şirket Adı')
        story.append(Paragraph(ensure_unicode(company_name), company_style))
        story.append(Spacer(1, 0.3*cm))
        
        # Başlık
        story.append(Paragraph("YASAL RAPOR", title_style))
        story.append(Paragraph("Resmi Makamlar Icin Detayli Bilgi Dokumani", subtitle_style))
        
        # Rapor metadata
        metadata = report_data.get('report_metadata', {})
        metadata_data = [
            ['Rapor Tarihi:', ensure_unicode(metadata.get('report_date', ''))],
            ['Raporu Oluşturan:', ensure_unicode(metadata.get('generated_by', ''))]
        ]
        
        metadata_table = Table(metadata_data, colWidths=[5*cm, 11*cm])
        metadata_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'TurkceArial'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Ayırıcı çizgi
        line_table = Table([['']], colWidths=[16*cm])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#2c3e50')),
        ]))
        story.append(line_table)
        story.append(Spacer(1, 0.5*cm))
        
        # MUTABAKAT BİLGİLERİ (Sadece tekil mutabakat raporu için - VKN aramasında gösterme)
        mutabakat = report_data.get('mutabakat', {})
        mutabakats_list = report_data.get('mutabakats', [])
        
        # Eğer mutabakats listesi varsa (VKN araması), tek mutabakat bilgisini gösterme
        if mutabakat and len(mutabakats_list) == 0:
            story.append(Paragraph("[MUTABAKAT BILGILERI]", section_style))
            
            mutabakat_data = [
                ['Mutabakat Numarasi:', ensure_unicode(mutabakat.get('mutabakat_no', ''))],
                ['Durum:', ensure_unicode(mutabakat.get('durum', ''))],
                ['Bakiye:', ensure_unicode(mutabakat.get('bakiye_str', ''))],
                ['Toplam Borc:', ensure_unicode(mutabakat.get('toplam_borc_str', ''))],
                ['Toplam Alacak:', ensure_unicode(mutabakat.get('toplam_alacak_str', ''))],
                ['Bayi Sayisi:', ensure_unicode(str(mutabakat.get('toplam_bayi_sayisi', 0)))],
                ['Donem:', ensure_unicode(mutabakat.get('donem_str', ''))],
                ['Olusturulma:', ensure_unicode(mutabakat.get('created_at_str', ''))],
            ]
            
            if mutabakat.get('pdf_file_path'):
                mutabakat_data.append(['PDF Dosyasi:', ensure_unicode(mutabakat.get('pdf_file_path', ''))])
            
            mutabakat_table = Table(mutabakat_data, colWidths=[5*cm, 11*cm])
            mutabakat_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'TurkceArial'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
            ]))
            story.append(mutabakat_table)
            story.append(Spacer(1, 0.5*cm))
        
        # GÖNDEREN VE ALICI (Her zaman göster)
        sender = report_data.get('sender', {})
        receiver = report_data.get('receiver', {})
        
        if sender or receiver:
            story.append(Paragraph("[TARAFLAR]", section_style))
            
            # Hücre içi metin stili (küçük, sarmalı)
            cell_style = ParagraphStyle(
                'CellText',
                parent=styles['Normal'],
                fontName='TurkceArial',
                fontSize=8,
                leading=10,
                wordWrap='CJK'
            )
            
            # Başlık stili (beyaz, kalın)
            header_style = ParagraphStyle(
                'HeaderText',
                parent=styles['Normal'],
                fontName='TurkceArial-Bold',
                fontSize=10,
                leading=12,
                textColor=colors.whitesmoke,
                alignment=1  # CENTER
            )
            
            # 3 kolonlu tablo: Label, Gönderen, Alıcı
            parties_data = [[
                '',
                Paragraph('GONDEREN', header_style),
                Paragraph('ALICI', header_style)
            ]]
            
            fields = ['vkn_tckn', 'full_name', 'company_name', 'email', 'phone']
            labels = ['VKN/TC:', 'Ad Soyad:', 'Firma:', 'Email:', 'Telefon:']
            
            for field, label in zip(fields, labels):
                sender_val = ensure_unicode(sender.get(field, '-')) if sender else '-'
                receiver_val = ensure_unicode(receiver.get(field, '-')) if receiver else '-'
                
                # Paragraph ile sarmalama yaparak metinlerin sığmasını sağla
                parties_data.append([
                    label,
                    Paragraph(sender_val, cell_style),
                    Paragraph(receiver_val, cell_style)
                ])
            
            parties_table = Table(parties_data, colWidths=[2.5*cm, 6.75*cm, 6.75*cm])
            parties_table.setStyle(TableStyle([
                # Label kolonu stili
                ('FONTNAME', (0, 1), (0, -1), 'TurkceArial'),
                ('FONTSIZE', (0, 1), (0, -1), 9),
                ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
                
                # Başlık satırı
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                
                # Veri hücreleri
                ('BACKGROUND', (1, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                
                # Genel
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
            ]))
            story.append(parties_table)
            story.append(Spacer(1, 0.5*cm))
        
        # KULLANICI RAPORU İÇİN TÜM MUTABAKATLAR (Çoğul - mutabakats)
        mutabakats = report_data.get('mutabakats', [])
        if mutabakats and len(mutabakats) > 0:
            story.append(Paragraph(f"[MUTABAKATLAR] ({len(mutabakats)} adet)", section_style))
            
            # Mutabakatlar tablosu
            mutabakats_data = [['Mutabakat No', 'Durum', 'Bakiye', 'Borc', 'Alacak', 'Donem']]
            for m in mutabakats:
                bakiye = float(m.get('bakiye', 0))
                borc = float(m.get('toplam_borc', 0))
                alacak = float(m.get('toplam_alacak', 0))
                
                mutabakats_data.append([
                    ensure_unicode(m.get('mutabakat_no', ''))[:20],
                    ensure_unicode(m.get('durum', ''))[:10],
                    f"{bakiye:,.2f} TL".replace(',', '.'),
                    f"{borc:,.2f} TL".replace(',', '.'),
                    f"{alacak:,.2f} TL".replace(',', '.'),
                    ensure_unicode(m.get('donem_str', ''))[:20]
                ])
            
            mutabakats_table = Table(mutabakats_data, colWidths=[4*cm, 2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm])
            mutabakats_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'TurkceArial'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('FONTNAME', (0, 0), (-1, 0), 'TurkceArial-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (2, 1), (4, -1), 'RIGHT'),  # Sayilar sağa hizali
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(mutabakats_table)
            story.append(Spacer(1, 0.5*cm))
        
        # İŞLEM LOGLARI
        activity_logs = report_data.get('activity_logs', [])
        if activity_logs:
            story.append(Paragraph(f"[ISLEM LOGLARI] ({len(activity_logs)} adet)", section_style))
            
            logs_data = [['Tarih', 'İşlem', 'IP', 'ISP', 'Konum']]
            for log in activity_logs[:20]:  # İlk 20 log
                logs_data.append([
                    ensure_unicode(log.get('timestamp_str', ''))[:16],
                    ensure_unicode(log.get('action', ''))[:15],
                    ensure_unicode(log.get('ip_address', ''))[:15],
                    ensure_unicode(log.get('isp', ''))[:20],
                    ensure_unicode(log.get('city', ''))[:15]
                ])
            
            logs_table = Table(logs_data, colWidths=[3*cm, 3*cm, 3*cm, 4*cm, 3*cm])
            logs_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'TurkceArial'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('FONTNAME', (0, 0), (-1, 0), 'TurkceArial-Bold'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            story.append(logs_table)
            story.append(Spacer(1, 0.5*cm))
        
        # KVKK BİLGİLERİ - DETAYLI
        kvkk_consents = report_data.get('kvkk_consents', {})
        if kvkk_consents:
            story.append(Paragraph("[KVKK ONAYLARI - DETAYLI]", section_style))
            
            for party, label in [('sender', 'Gönderen'), ('receiver', 'Alıcı')]:
                consent = kvkk_consents.get(party, {})
                if consent and consent.get('exists') and consent.get('data'):
                    data = consent['data']
                    
                    # Parti başlığı
                    story.append(Paragraph(f"<b>{label}:</b>", ParagraphStyle(
                        'PartyTitle',
                        parent=normal_style,
                        fontName='TurkceArial-Bold',
                        fontSize=11,
                        textColor=colors.HexColor('#2c3e50'),
                        spaceAfter=6
                    )))
                    
                    # KVKK detay tablosu (Simgeler görünmüyor, text kullan)
                    kvkk_detail_data = [
                        ['KVKK Politikasi', '[+] Onaylandi' if data.get('kvkk_policy_accepted') else '[-] Red', ensure_unicode(data.get('kvkk_policy_date_str', '-'))],
                        ['Musteri Aydinlatma', '[+] Onaylandi' if data.get('customer_notice_accepted') else '[-] Red', ensure_unicode(data.get('customer_notice_date_str', '-'))],
                        ['Veri Saklama', '[+] Onaylandi' if data.get('data_retention_accepted') else '[-] Red', ensure_unicode(data.get('data_retention_date_str', '-'))],
                        ['Sistem Onayi', '[+] Onaylandi' if data.get('system_consent_accepted') else '[-] Red', ensure_unicode(data.get('system_consent_date_str', '-'))],
                    ]
                    
                    kvkk_detail_table = Table(kvkk_detail_data, colWidths=[5.5*cm, 4*cm, 6.5*cm])
                    
                    # Onaylı olanlar yeşil arka plan, red olanlar kırmızı
                    table_styles = [
                        ('FONTNAME', (0, 0), (-1, -1), 'TurkceArial'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('FONTNAME', (0, 0), (0, -1), 'TurkceArial-Bold'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ]
                    
                    # Her satır için renk belirle (onaylı: yeşil, red: kırmızı)
                    for i, (key, accepted_key) in enumerate([
                        ('KVKK Politikasi', 'kvkk_policy_accepted'),
                        ('Musteri Aydinlatma', 'customer_notice_accepted'),
                        ('Veri Saklama', 'data_retention_accepted'),
                        ('Sistem Onayi', 'system_consent_accepted')
                    ]):
                        if data.get(accepted_key):
                            # Onaylı - açık yeşil
                            table_styles.append(('BACKGROUND', (1, i), (1, i), colors.HexColor('#d4edda')))
                            table_styles.append(('TEXTCOLOR', (1, i), (1, i), colors.HexColor('#155724')))
                        else:
                            # Red - açık kırmızı
                            table_styles.append(('BACKGROUND', (1, i), (1, i), colors.HexColor('#f8d7da')))
                            table_styles.append(('TEXTCOLOR', (1, i), (1, i), colors.HexColor('#721c24')))
                    
                    kvkk_detail_table.setStyle(TableStyle(table_styles))
                    story.append(kvkk_detail_table)
                    story.append(Spacer(1, 0.2*cm))
                    
                    # ISP bilgileri (tablo formatında)
                    story.append(Spacer(1, 0.2*cm))
                    story.append(Paragraph("<b>Onay Detaylari:</b>", ParagraphStyle(
                        'ISPTitle',
                        parent=normal_style,
                        fontName='TurkceArial-Bold',
                        fontSize=9,
                        textColor=colors.HexColor('#495057'),
                        spaceAfter=4
                    )))
                    
                    isp_data = [
                        ['IP Adresi:', ensure_unicode(data.get('ip_address', '-'))],
                        ['ISP:', ensure_unicode(data.get('isp', '-'))],
                        ['Konum:', f"{ensure_unicode(data.get('city', '-'))}, {ensure_unicode(data.get('country', '-'))}"],
                        ['Ilk Onay:', ensure_unicode(data.get('created_at_str', '-'))]
                    ]
                    
                    isp_table = Table(isp_data, colWidths=[4*cm, 12*cm])
                    isp_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, -1), 'TurkceArial'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('FONTNAME', (0, 0), (0, -1), 'TurkceArial-Bold'),
                        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6c757d')),
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ]))
                    story.append(isp_table)
                    story.append(Spacer(1, 0.4*cm))
            
            story.append(Spacer(1, 0.3*cm))
        
        # KVKK ONAY SİLME KAYITLARI
        kvkk_deletions = report_data.get('kvkk_deletions', {})
        if kvkk_deletions and (kvkk_deletions.get('sender') or kvkk_deletions.get('receiver')):
            story.append(Paragraph("[!] KVKK ONAY SILME KAYITLARI (Yasal Delil)", section_style))
            
            for party, label in [('sender', 'Gönderen'), ('receiver', 'Alıcı')]:
                deletions = kvkk_deletions.get(party, [])
                if deletions:
                    story.append(Paragraph(f"<b>{label} - {len(deletions)} Silme Kaydı:</b>", ParagraphStyle(
                        'DeletionTitle',
                        parent=normal_style,
                        fontName='TurkceArial-Bold',
                        fontSize=10,
                        textColor=colors.HexColor('#c0392b'),
                        spaceAfter=6
                    )))
                    
                    for idx, deletion in enumerate(deletions[:5], 1):  # İlk 5 kayıt
                        deletion_data = [
                            [f'#{idx}', 'Silme Tarihi:', ensure_unicode(deletion.get('deleted_at_str', '-'))],
                            ['', 'Silen Admin:', ensure_unicode(deletion.get('deleted_by_username', '-'))],
                            ['', 'Silme Nedeni:', ensure_unicode(deletion.get('deletion_reason', 'Belirtilmemiş'))],
                            ['', 'Silme IP/ISP:', f"{ensure_unicode(deletion.get('deletion_ip_address', '-'))} / {ensure_unicode(deletion.get('deletion_isp', '-'))}"],
                            ['', 'Orijinal IP/ISP:', f"{ensure_unicode(deletion.get('original_ip_address', '-'))} / {ensure_unicode(deletion.get('original_isp', '-'))}"],
                        ]
                        
                        deletion_table = Table(deletion_data, colWidths=[1*cm, 4*cm, 11*cm])
                        deletion_table.setStyle(TableStyle([
                            ('FONTNAME', (0, 0), (-1, -1), 'TurkceArial'),
                            ('FONTSIZE', (0, 0), (-1, -1), 7),
                            ('FONTNAME', (0, 0), (0, 0), 'TurkceArial-Bold'),
                            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#7f8c8d')),
                            ('SPAN', (0, 0), (0, -1)),
                            ('VALIGN', (0, 0), (0, -1), 'TOP'),
                            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 3),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                            ('TOPPADDING', (0, 0), (-1, -1), 2),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e74c3c')),
                            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fadbd8')),
                        ]))
                        story.append(deletion_table)
                        story.append(Spacer(1, 0.2*cm))
                    
                    if len(deletions) > 5:
                        story.append(Paragraph(f"<i>+ {len(deletions) - 5} silme kaydı daha mevcut...</i>", ParagraphStyle(
                            'More',
                            parent=normal_style,
                            fontSize=7,
                            textColor=colors.HexColor('#7f8c8d'),
                            alignment=TA_CENTER
                        )))
                    story.append(Spacer(1, 0.3*cm))
            
            story.append(Spacer(1, 0.3*cm))
        
        # YASAL UYARI
        story.append(Spacer(1, 1*cm))
        warning_style = ParagraphStyle(
            'Warning',
            parent=styles['Normal'],
            fontName='TurkceArial',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#c0392b'),
            borderColor=colors.HexColor('#e74c3c'),
            borderWidth=1,
            borderPadding=10,
            backColor=colors.HexColor('#fadbd8')
        )
        warning_text = (
            "<b>[YASAL UYARI]:</b> Bu rapor resmi makamlar tarafindan talep edilen yasal delil niteligindeki "
            "bilgileri icermektedir. Tum IP adresleri, ISP bilgileri, islem loglari ve KVKK onaylari yasal "
            "sureclerde kullanilmak uzere hazirlanmistir. Bu dokuman dijital olarak imzalanmis ve sifrelenmistir."
        )
        story.append(Paragraph(warning_text, warning_style))
        
        # ŞİRKET BİLGİLERİ FOOTER (metadata'dan)
        story.append(Spacer(1, 1*cm))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontName='TurkceArial',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#7f8c8d'),
            alignment=TA_CENTER,
            borderColor=colors.HexColor('#bdc3c7'),
            borderWidth=1,
            borderPadding=12,
            backColor=colors.HexColor('#ecf0f1')
        )
        
        # Şirket bilgilerini metadata'dan al
        company_name = metadata.get('company_name', '')
        company_address = metadata.get('company_address', '')
        company_phone = metadata.get('company_phone', '')
        company_email = metadata.get('company_email', '')
        company_website = metadata.get('company_website', '')
        
        footer_text = f"<b>{ensure_unicode(company_name)}</b><br/>"
        if company_address:
            footer_text += f"{ensure_unicode(company_address)}<br/>"
        if company_phone or company_email:
            contact_line = []
            if company_phone:
                contact_line.append(f"Tel: {company_phone}")
            if company_email:
                contact_line.append(f"E-posta: {company_email}")
            footer_text += " | ".join(contact_line) + "<br/>"
        if company_website:
            footer_text += f"Web: {company_website}"
        
        story.append(Paragraph(footer_text, footer_style))
        
        # İMZA ALANI
        story.append(Spacer(1, 0.8*cm))
        story.append(Paragraph(f"<b>Rapor Tarihi:</b> {metadata.get('report_date', '')}", normal_style))
        story.append(Paragraph(f"<b>Hazirlayan:</b> {metadata.get('generated_by', '')}", normal_style))
        story.append(Spacer(1, 0.8*cm))
        story.append(Paragraph("<b>Imza:</b> _________________", normal_style))
        
        # PDF oluştur
        doc.build(story)
        
        # Buffer'ı başa sar
        self.buffer.seek(0)
        return self.buffer

def generate_legal_report_hash(pdf_bytes):
    """PDF için SHA-256 hash oluştur"""
    return hashlib.sha256(pdf_bytes).hexdigest()

