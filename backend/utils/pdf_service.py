"""
PDF Mutabakat Belgesi Oluşturma Servisi
Hukuki geçerliliği olan, dijital imzalı mutabakat belgeleri üretir.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import hashlib
import os
from io import BytesIO
import qrcode
from PIL import Image as PILImage
import pytz
from backend.models import UserRole

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
        # Font yolları (Docker container için)
        # Önce fonts/ klasöründe ara, yoksa sistem fontlarını kullan
        font_dir = "fonts"
        
        # Liberation Sans (Arial alternatifi, Türkçe Unicode destekli)
        arial_path = os.path.join(font_dir, "LiberationSans-Regular.ttf")
        arial_bold_path = os.path.join(font_dir, "LiberationSans-Bold.ttf")
        arial_italic_path = os.path.join(font_dir, "LiberationSans-Italic.ttf")
        
        # Fallback: Windows font yolları (local development için)
        if not os.path.exists(arial_path):
            arial_path = "C:/Windows/Fonts/arial.ttf"
        if not os.path.exists(arial_bold_path):
            arial_bold_path = "C:/Windows/Fonts/arialbd.ttf"
        if not os.path.exists(arial_italic_path):
            arial_italic_path = "C:/Windows/Fonts/ariali.ttf"
        
        if os.path.exists(arial_path):
            pdfmetrics.registerFont(TTFont('TurkceArial', arial_path, 'UTF-8'))
            print(f"[PDF] TurkceArial font yüklendi: {arial_path}")
        if os.path.exists(arial_bold_path):
            pdfmetrics.registerFont(TTFont('TurkceArial-Bold', arial_bold_path, 'UTF-8'))
            print(f"[PDF] TurkceArial-Bold font yüklendi: {arial_bold_path}")
        if os.path.exists(arial_italic_path):
            pdfmetrics.registerFont(TTFont('TurkceArial-Italic', arial_italic_path, 'UTF-8'))
            print(f"[PDF] TurkceArial-Italic font yüklendi: {arial_italic_path}")
        
        FONTS_REGISTERED = True
        return True
    except Exception as e:
        print(f"[PDF] Font yükleme uyarısı: {e}")
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


class MutabakatPDFGenerator:
    """Hukuki Mutabakat PDF Belgesi Oluşturucu"""
    
    def __init__(self):
        self.buffer = BytesIO()
        self.pagesize = A4
        self.width, self.height = A4
    
    def _create_qr_code(self, mutabakat_no, pdf_hash=None):
        """QR kod oluştur (doğrulama URL'si için)"""
        try:
            # Doğrulama URL'si (frontend verify sayfası)
            # Production'da domain güncellenecek
            base_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            verify_url = f"{base_url}/verify/mutabakat/{mutabakat_no}"
            if pdf_hash:
                verify_url += f"?hash={pdf_hash[:32]}"
            
            # QR kod oluştur
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=1,
            )
            qr.add_data(verify_url)
            qr.make(fit=True)
            
            # PIL Image olarak al
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # BytesIO'ya kaydet
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            print(f"[PDF] QR kod olusturuldu: {verify_url[:70]}...")
            return qr_buffer
        except Exception as e:
            print(f"[PDF] QR kod olusturulamadi: {e}")
            return None
        
    def _create_styles(self):
        """PDF stilleri oluştur (Türkçe karakter destekli)"""
        styles = getSampleStyleSheet()
        
        # Türkçe font kontrolü (UTF-8 destekli)
        if FONTS_LOADED:
            title_font = 'TurkceArial-Bold'
            heading_font = 'TurkceArial-Bold'
            body_font = 'TurkceArial'
            legal_font = 'TurkceArial-Italic'
        else:
            # Fallback to Helvetica
            title_font = 'Helvetica-Bold'
            heading_font = 'Helvetica-Bold'
            body_font = 'Helvetica'
            legal_font = 'Helvetica-Oblique'
        
        # Başlık stili
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a365d'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=title_font
        ))
        
        # Alt başlık
        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2c5282'),
            spaceAfter=12,
            spaceBefore=20,
            fontName=heading_font
        ))
        
        # Normal metin
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=14,
            fontName=body_font
        ))
        
        # Küçük metin
        styles.add(ParagraphStyle(
            name='SmallText',
            parent=styles['BodyText'],
            fontSize=8,
            textColor=colors.HexColor('#4a5568'),
            spaceAfter=6,
            fontName=body_font
        ))
        
        # Kanun maddesi
        styles.add(ParagraphStyle(
            name='LegalText',
            parent=styles['BodyText'],
            fontSize=9,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=8,
            leftIndent=20,
            fontName=legal_font
        ))
        
        return styles
    
    def _generate_digital_signature(self, mutabakat_data, action_data):
        """
        Dijital imza hash'i oluştur
        
        NOT: Hash sadece DEĞİŞMEZ verilerle oluşturulur.
        Timestamp ve IP adresi hash'e DAHİL EDİLMEZ çünkü:
        - PDF her indirildiğinde timestamp değişir
        - IP adresi sonradan doğrulanamaz
        
        Hash'e dahil olan veriler:
        - mutabakat_no (benzersiz)
        - sender_company (şirket adı)
        - receiver_company (şirket adı)
        - toplam_borc (tutar)
        - toplam_alacak (tutar)
        - action (ONAYLANDI/REDDEDİLDİ)
        """
        data_string = f"{mutabakat_data['mutabakat_no']}"
        data_string += f"{mutabakat_data['sender_company']}"
        data_string += f"{mutabakat_data['receiver_company']}"
        data_string += f"{mutabakat_data['toplam_borc']}"
        data_string += f"{mutabakat_data['toplam_alacak']}"
        data_string += f"{action_data['action']}"
        # NOT: timestamp ve ip_address hash'e dahil edilmiyor
        
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def generate_mutabakat_pdf(self, mutabakat_data, action_data):
        """
        Mutabakat PDF'i oluştur
        
        Args:
            mutabakat_data: Mutabakat bilgileri
            action_data: İşlem bilgileri (onay/red, tarih, IP, vb.)
        """
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=self.pagesize,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = self._create_styles()
        story = []
        
        # Font kontrolü (Türkçe için UTF-8 destekli Arial)
        if FONTS_LOADED:
            table_font = 'TurkceArial'
            table_font_bold = 'TurkceArial-Bold'
        else:
            table_font = 'Helvetica'
            table_font_bold = 'Helvetica-Bold'
        
        # Dijital imza oluştur
        digital_signature = self._generate_digital_signature(mutabakat_data, action_data)
        
        # ========== LOGO VE QR KOD ==========
        # Proje kök dizinini bul
        current_file = os.path.abspath(__file__)
        utils_dir = os.path.dirname(current_file)  # backend/utils
        backend_dir = os.path.dirname(utils_dir)   # backend
        project_root = os.path.dirname(backend_dir) # root
        
        # Logo yolunu al (şirket logosu veya default)
        company_logo = mutabakat_data.get('company_logo')
        if company_logo:
            # Şirket logosu belirtilmiş
            logo_path = os.path.join(project_root, "frontend", "public", company_logo)
        else:
            # Default Dino logosu
            logo_path = os.path.join(project_root, "frontend", "public", "dino-logo.png")
        
        print(f"[PDF] Logo aranıyor: {logo_path}")
        print(f"[PDF] Logo var mı? {os.path.exists(logo_path)}")
        
        # Logo ve QR kod için header tablosu
        header_elements = []
        
        # Logo (sol taraf)
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=3.5*cm, height=3.5*cm, kind='proportional')
                header_elements.append(logo)
                print(f"[PDF] [OK] Logo eklendi!")
            except Exception as e:
                print(f"[PDF] [!] Logo yükleme hatası: {e}")
                # Logo yerine text-based header (şirket ismiyle)
                company_name = mutabakat_data.get('company_info', {}).get('full_name', 'DINO GIDA')
                logo_style = ParagraphStyle(
                    'LogoText',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.HexColor('#667eea'),
                    fontName=table_font_bold,
                    alignment=TA_CENTER
                )
                logo_text = Paragraph(ensure_unicode(f"<b>{company_name}<br/>E-MUTABAKAT</b>"), logo_style)
                header_elements.append(logo_text)
        else:
            print(f"[PDF] [!] Logo bulunamadı, text logo kullaniliyor")
            # Logo yerine text-based header (şirket ismiyle)
            company_name = mutabakat_data.get('company_info', {}).get('full_name', 'DINO GIDA')
            logo_style = ParagraphStyle(
                'LogoText',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#667eea'),
                fontName=table_font_bold,
                alignment=TA_CENTER
            )
            logo_text = Paragraph(ensure_unicode(f"<b>{company_name}<br/>E-MUTABAKAT</b>"), logo_style)
            header_elements.append(logo_text)
        
        # Boş alan (orta)
        header_elements.append(Paragraph("", styles['Normal']))
        
        # QR Kod (sağ taraf) - hash sadece doğrulama için
        pdf_hash = hashlib.sha256(mutabakat_data['mutabakat_no'].encode()).hexdigest()
        qr_buffer = self._create_qr_code(mutabakat_data['mutabakat_no'], pdf_hash)
        if qr_buffer:
            try:
                qr_image = Image(qr_buffer, width=3*cm, height=3*cm)
                header_elements.append(qr_image)
                print(f"[PDF] [OK] QR kod eklendi!")
            except Exception as e:
                print(f"[PDF] [!] QR kod yükleme hatası: {e}")
                header_elements.append(Paragraph("", styles['Normal']))
        else:
            header_elements.append(Paragraph("", styles['Normal']))
        
        # Header tablosu (Logo - Boşluk - QR Kod)
        header_table = Table([header_elements], colWidths=[4*cm, 9*cm, 4*cm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),    # Logo sola
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # Orta boş
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),   # QR kod sağa
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 0.3*cm))
        
        # QR Kod Açıklaması
        qr_info_style = ParagraphStyle(
            name='QRInfo',
            alignment=TA_RIGHT,
            fontSize=7,
            textColor=colors.HexColor('#718096'),
            fontName=table_font if FONTS_LOADED else 'Helvetica',
            spaceAfter=4
        )
        story.append(Paragraph(
            ensure_unicode("QR kodu okutarak belgeyi doğrulayabilirsiniz"),
            qr_info_style
        ))
        story.append(Spacer(1, 0.3*cm))
        
        # ========== BAŞLIK ==========
        story.append(Paragraph(
            f"<b>{ensure_unicode(mutabakat_data['sender_company'])}</b>",
            styles['CustomTitle']
        ))
        
        story.append(Paragraph(
            ensure_unicode("ELEKTRONİK CARİ HESAP MUTABAKAT BELGESİ"),
            styles['CustomTitle']
        ))
        
        story.append(Spacer(1, 0.5*cm))
        
        # ========== BELGE BİLGİLERİ ==========
        belge_data = [
            [ensure_unicode('Mutabakat No:'), ensure_unicode(mutabakat_data['mutabakat_no'])],
            [ensure_unicode('Belge Tarihi:'), get_turkey_time().strftime('%d.%m.%Y %H:%M:%S')],
            [ensure_unicode('Dönem:'), f"{mutabakat_data['donem_baslangic']} - {mutabakat_data['donem_bitis']}"],
        ]
        
        belge_table = Table(belge_data, colWidths=[5*cm, 12*cm])
        belge_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#edf2f7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), table_font_bold),
            ('FONTNAME', (1, 0), (1, -1), table_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(belge_table)
        story.append(Spacer(1, 0.5*cm))
        
        # ========== TARAFLAR ==========
        story.append(Paragraph(ensure_unicode("TARAFLAR"), styles['CustomHeading']))
        
        # Hücre içi metin stili (küçük, sarmalı)
        cell_style = ParagraphStyle(
            'CellText',
            parent=styles['Normal'],
            fontName=table_font,
            fontSize=8,
            leading=10,
            wordWrap='CJK'
        )
        
        # Başlık stili
        header_style = ParagraphStyle(
            'HeaderText',
            parent=styles['Normal'],
            fontName=table_font_bold,
            fontSize=9,
            leading=11,
            alignment=TA_CENTER
        )
        
        taraf_data = [
            ['', Paragraph(ensure_unicode('Gönderen (Şirket)'), header_style), Paragraph(ensure_unicode('Alıcı (Müşteri/Tedarikçi)'), header_style)],
            [ensure_unicode('Ünvan:'), Paragraph(ensure_unicode(mutabakat_data['sender_company']), cell_style), Paragraph(ensure_unicode(mutabakat_data['receiver_company']), cell_style)],
            [ensure_unicode('VKN/TC:'), Paragraph(ensure_unicode(mutabakat_data.get('sender_vkn', '-')), cell_style), Paragraph(ensure_unicode(mutabakat_data.get('receiver_vkn', '-')), cell_style)],
            [ensure_unicode('Yetkili:'), Paragraph(ensure_unicode(mutabakat_data.get('sender_contact', '-')), cell_style), Paragraph(ensure_unicode(mutabakat_data.get('receiver_contact', '-')), cell_style)],
            [ensure_unicode('Telefon:'), Paragraph(ensure_unicode(mutabakat_data.get('sender_phone', '-')), cell_style), Paragraph(ensure_unicode(mutabakat_data.get('receiver_phone', '-')), cell_style)],
            [ensure_unicode('Email:'), Paragraph(ensure_unicode(mutabakat_data.get('sender_email', '-')), cell_style), Paragraph(ensure_unicode(mutabakat_data.get('receiver_email', '-')), cell_style)],
        ]
        
        taraf_table = Table(taraf_data, colWidths=[2.5*cm, 7.25*cm, 7.25*cm])
        taraf_table.setStyle(TableStyle([
            # Başlık satırı
            ('BACKGROUND', (1, 0), (2, 0), colors.HexColor('#4299e1')),
            ('TEXTCOLOR', (1, 0), (2, 0), colors.whitesmoke),
            
            # Label kolonu (ilk kolon)
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#edf2f7')),
            ('ALIGN', (0, 1), (0, -1), 'RIGHT'),  # Label sağa hizalı
            ('FONTNAME', (0, 1), (0, -1), table_font_bold),
            
            # Veri kolonları
            ('ALIGN', (1, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Üstten hizalama
            ('FONTNAME', (0, 0), (0, 0), table_font),  # Boş hücre
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(taraf_table)
        story.append(Spacer(1, 0.5*cm))
        
        # ========== FİNANSAL ÖZET ==========
        story.append(Paragraph(ensure_unicode("FİNANSAL ÖZET"), styles['CustomHeading']))
        
        finansal_data = [
            [ensure_unicode('AÇIKLAMA'), ensure_unicode('TUTAR (₺)')],
            [ensure_unicode('Toplam Borç'), f"{mutabakat_data['toplam_borc']:,.2f}"],
            [ensure_unicode('Toplam Alacak'), f"{mutabakat_data['toplam_alacak']:,.2f}"],
            [ensure_unicode('Net Bakiye'), f"{mutabakat_data['bakiye']:,.2f}"],
        ]
        
        finansal_table = Table(finansal_data, colWidths=[12*cm, 5*cm])
        finansal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#edf2f7')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), table_font_bold),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        story.append(finansal_table)
        story.append(Spacer(1, 0.5*cm))
        
        # ========== BAYİ DETAYLARI (VKN Bazlı Mutabakat için) ==========
        if mutabakat_data.get('bayi_detaylari') and len(mutabakat_data['bayi_detaylari']) > 0:
            story.append(Paragraph(ensure_unicode("BAYİ DETAYLARI"), styles['CustomHeading']))
            
            # VKN bilgisi varsa göster
            if mutabakat_data.get('receiver_vkn'):
                vkn_info = Paragraph(
                    f"<i>{ensure_unicode('VKN/TC: ' + mutabakat_data['receiver_vkn'])} | "
                    f"{ensure_unicode('Toplam Bayi: ' + str(mutabakat_data.get('toplam_bayi_sayisi', 0)))}</i>",
                    styles['Normal']
                )
                story.append(vkn_info)
                story.append(Spacer(1, 0.2*cm))
            
            # Bayi detayları tablosu
            bayi_header = [ensure_unicode('Bayi Kodu'), ensure_unicode('Bayi Adı'), ensure_unicode('Bakiye (₺)')]
            bayi_rows = [bayi_header]
            
            for bayi in mutabakat_data['bayi_detaylari']:
                # Uzun bayi isimlerini Paragraph ile wrap et
                bayi_adi_para = Paragraph(
                    ensure_unicode(bayi['bayi_adi']),
                    ParagraphStyle(
                        'BayiAdi',
                        parent=styles['Normal'],
                        fontName=table_font,
                        fontSize=9,
                        leading=11,
                        wordWrap='LTR'
                    )
                )
                bayi_rows.append([
                    ensure_unicode(bayi['bayi_kodu']),
                    bayi_adi_para,
                    f"{bayi['bakiye']:,.2f}"
                ])
            
            # Toplam satırı
            bayi_rows.append([
                ensure_unicode('TOPLAM'),
                '',
                f"{mutabakat_data['bakiye']:,.2f}"
            ])
            
            bayi_table = Table(bayi_rows, colWidths=[2.5*cm, 11*cm, 3.5*cm])
            bayi_table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4299e1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), table_font_bold),
                # Body
                ('FONTNAME', (0, 1), (-1, -2), table_font),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Üstten hizala
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                # Toplam satırı
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#edf2f7')),
                ('FONTNAME', (0, -1), (-1, -1), table_font_bold),
                ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.grey),
            ]))
            
            story.append(bayi_table)
            story.append(Spacer(1, 0.5*cm))
        
        # ========== MUTABAKAT DURUMU ==========
        story.append(Paragraph(ensure_unicode("MUTABAKAT DURUMU"), styles['CustomHeading']))
        
        if action_data['action'] == 'ONAYLANDI':
            durum_color = colors.HexColor('#48bb78')
            durum_text = ensure_unicode(">>> ONAYLANDI <<<")  # Çift ok ile vurgulu
            aciklama = ensure_unicode("Yukarıda belirtilen dönem ve tutarlar tarafımızca incelenmiş ve kayıtlarımızla mutabık olduğu tespit edilmiştir.")
        else:
            durum_color = colors.HexColor('#f56565')
            durum_text = ensure_unicode(">>> REDDEDİLDİ <<<")  # Çift ok ile vurgulu
            red_nedeni = ensure_unicode(action_data.get('red_nedeni', 'Belirtilmemiş'))
            aciklama = f"Yukarıda belirtilen tutarlar tarafımızca kontrol edilmiş ve kayıtlarımızla uyuşmadığı tespit edilmiştir.<br/><br/><b>Red Nedeni:</b> {red_nedeni}"
        
        durum_data = [
            [durum_text],
        ]
        
        durum_table = Table(durum_data, colWidths=[17*cm])
        durum_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), durum_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), table_font_bold),
            ('FONTSIZE', (0, 0), (-1, -1), 20),  # Daha büyük font
            ('BOTTOMPADDING', (0, 0), (-1, -1), 18),  # Daha fazla padding
            ('TOPPADDING', (0, 0), (-1, -1), 18),
        ]))
        
        story.append(durum_table)
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(aciklama, styles['CustomBody']))
        story.append(Spacer(1, 0.5*cm))
        
        # ========== İŞLEM BİLGİLERİ ==========
        story.append(Paragraph(ensure_unicode("İŞLEM BİLGİLERİ VE DİJİTAL İMZA"), styles['CustomHeading']))
        
        # IP bilgilerini ayrıştır (dict veya string olabilir)
        ip_info = action_data.get('ip_info', {})
        if isinstance(ip_info, str):
            # Eski format: sadece IP string
            ip_display = ip_info
            isp_info = None
        else:
            # Yeni format: ISP bilgili dict
            ip_display = ip_info.get('ip', action_data.get('ip_address', 'Bilinmiyor'))
            isp_info = f"{ip_info.get('isp', 'Bilinmiyor')} - {ip_info.get('city', '')}, {ip_info.get('country', '')}"
        
        islem_data = [
            [ensure_unicode('İşlem Yapan:'), ensure_unicode(action_data['user_name'])],
            [ensure_unicode('İşlem Tarihi:'), action_data['timestamp']],
            [ensure_unicode('IP Adresi:'), ensure_unicode(ip_display)],
        ]
        
        # ISP bilgisi varsa ekle (yasal delil)
        if isp_info and isp_info != 'Bilinmiyor - , ':
            islem_data.append([ensure_unicode('İnternet Sağlayıcı (ISP):'), ensure_unicode(isp_info)])
        
        islem_data.append([ensure_unicode('Dijital İmza (SHA-256):'), digital_signature[:32] + '...'])
        
        islem_table = Table(islem_data, colWidths=[5*cm, 12*cm])
        islem_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fff5f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), table_font_bold),
            ('FONTNAME', (1, 0), (1, -1), table_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(islem_table)
        story.append(Spacer(1, 1*cm))
        
        # ========== HUKUKİ DAYANAK ==========
        story.append(Paragraph(ensure_unicode("HUKUKİ DAYANAK"), styles['CustomHeading']))
        
        story.append(Paragraph(
            ensure_unicode("<b>1. Türk Ticaret Kanunu (TTK) - Kanun No: 6102</b>"),
            styles['CustomBody']
        ))
        story.append(Paragraph(
            ensure_unicode("Madde 18/3: Ticari defterler ve belgeler, Türkiye'de bulunan ve kanuni yollara başvurma hakkı saklı kalmak kaydıyla, aksine delil getirilinceye kadar, sicile kayıtlı tacirler arasındaki ticari ilişkilerden doğan davalarında delil teşkil eder."),
            styles['LegalText']
        ))
        story.append(Paragraph(
            ensure_unicode("Madde 93: Mutabakat veya itirazınızı 7 gün içinde bildirmediğiniz takdirde T.T.K'nun 93. maddesi gereğince mutabık sayılacağınızı hatırlatırız."),
            styles['LegalText']
        ))
        
        story.append(Paragraph(
            ensure_unicode("<b>2. Türk Borçlar Kanunu (TBK) - Kanun No: 6098</b>"),
            styles['CustomBody']
        ))
        story.append(Paragraph(
            ensure_unicode("Madde 88: Alacaklı ile borçlu, borç ilişkisinin kapsamı ve içeriği hakkında mutabakata vardıklarında, bu mutabakat sözleşmesi hükmündedir."),
            styles['LegalText']
        ))
        
        story.append(Paragraph(
            ensure_unicode("<b>3. Elektronik İmza Kanunu - Kanun No: 5070</b>"),
            styles['CustomBody']
        ))
        story.append(Paragraph(
            ensure_unicode("Madde 5: Güvenli elektronik imza, elle atılan imza ile aynı hukuki sonucu doğurur. Bu belge, elektronik ortamda oluşturulmuş ve kriptografik hash ile korunmaktadır."),
            styles['LegalText']
        ))
        
        story.append(Paragraph(
            ensure_unicode("<b>4. Ticari Defterlerin Tutulma ve Saklama Esasları - VUK</b>"),
            styles['CustomBody']
        ))
        story.append(Paragraph(
            ensure_unicode("Vergi Usul Kanunu Madde 253: Ticari defter kayıtları, mahkemelerce aksi sabit oluncaya kadar delil olarak kabul edilir. Bu mutabakat belgesi, taraflarca kabul edilen cari hesap durumunu gösterir."),
            styles['LegalText']
        ))
        
        story.append(Spacer(1, 1*cm))
        
        # ========== KURUMSAL BİLGİLENDİRME VE DİJİTAL İMZA ==========
        corporate_divider = ParagraphStyle(
            name='CorporateDivider',
            alignment=TA_CENTER,
            fontSize=9,
            textColor=colors.HexColor('#2c5282'),
            fontName=table_font_bold,
            spaceAfter=8
        )
        
        story.append(Paragraph(
            "═════════════════════════════════════════════════════════════════",
            corporate_divider
        ))
        
        # Elektronik belge bilgilendirmesi
        electronic_notice = ParagraphStyle(
            name='ElectronicNotice',
            alignment=TA_CENTER,
            fontSize=9,
            textColor=colors.HexColor('#1a365d'),
            fontName=table_font,
            spaceAfter=12,
            leading=14
        )
        
        story.append(Paragraph(
            ensure_unicode(
                "<b>ELEKTRONİK MUTABAKAT BELGESİ</b><br/>"
                "Bu belge elektronik ortamda oluşturulmuş olup, dijital imza ile güvence altına alınmıştır.<br/>"
                "Belgenin fiziksel imzaya ihtiyacı bulunmamaktadır. (5070 sayılı Elektronik İmza Kanunu)"
            ),
            electronic_notice
        ))
        
        story.append(Spacer(1, 0.5*cm))
        
        # Şirket bilgileri (Kurumsal footer)
        corporate_footer_style = ParagraphStyle(
            name='CorporateFooter',
            alignment=TA_CENTER,
            fontSize=10,
            textColor=colors.HexColor('#2c5282'),
            fontName=table_font_bold,
            spaceAfter=6
        )
        
        corporate_address_style = ParagraphStyle(
            name='CorporateAddress',
            alignment=TA_CENTER,
            fontSize=9,
            textColor=colors.HexColor('#4a5568'),
            fontName=table_font,
            spaceAfter=4,
            leading=12
        )
        
        # Şirket bilgileri (dinamik)
        company_full_name = mutabakat_data.get('company_info', {}).get('full_name', 'Dino Gıda San. Tic. Ltd. Şti.')
        company_address = mutabakat_data.get('company_info', {}).get('address', 'Görece Cumhuriyet Mah. Gülçırpı Cad. No:19<br/>35473 Menderes / İzmir')
        company_phone = mutabakat_data.get('company_info', {}).get('phone', '0850 220 45 66')
        company_email = mutabakat_data.get('company_info', {}).get('email', 'info@dinogida.com.tr')
        company_website = mutabakat_data.get('company_info', {}).get('website', 'www.dinogida.com.tr')
        
        story.append(Paragraph(
            ensure_unicode(f"<b>{company_full_name}</b>"),
            corporate_footer_style
        ))
        
        if company_address:
            story.append(Paragraph(
                ensure_unicode(company_address),
                corporate_address_style
            ))
        
        story.append(Paragraph(
            ensure_unicode(
                f"Tel: <b>{company_phone}</b> | E-posta: {company_email}<br/>"
                f"Web: {company_website}"
            ),
            corporate_address_style
        ))
        
        story.append(Spacer(1, 0.3*cm))
        
        story.append(Paragraph(
            "═════════════════════════════════════════════════════════════════",
            corporate_divider
        ))
        
        # ========== DİJİTAL İMZA BİLGİSİ ==========
        story.append(Paragraph(
            ensure_unicode(
                f"Bu belge {get_turkey_time().strftime('%d.%m.%Y %H:%M:%S')} tarihinde elektronik ortamda oluşturulmuş olup, "
                f"dijital imza ile korunmaktadır. Belgenin doğruluğu sistem kayıtlarından teyit edilebilir. "
                f"Belge referans numarası: {mutabakat_data['mutabakat_no']}"
            ),
            styles['SmallText']
        ))
        
        story.append(Paragraph(
            ensure_unicode(f"<b>Tam Dijital İmza (SHA-256):</b> {digital_signature}"),
            styles['SmallText']
        ))
        
        story.append(Spacer(1, 0.3*cm))
        
        # ========== DOĞRULAMA BİLGİSİ (MAHKEME/YASAL OTORİTELER İÇİN) ==========
        dogrulama_divider_style = ParagraphStyle(
            name='DogrulamaDividerStyle',
            alignment=TA_CENTER,
            fontSize=8,
            textColor=colors.HexColor('#2d3748'),
            fontName=table_font
        )
        
        dogrulama_title_style = ParagraphStyle(
            name='DogrulamaTitleStyle',
            alignment=TA_CENTER,
            fontSize=8,
            textColor=colors.HexColor('#2d3748'),
            fontName=table_font_bold,
            spaceAfter=6
        )
        
        dogrulama_text_style = ParagraphStyle(
            name='DogrulamaTextStyle',
            parent=styles['SmallText'],
            fontSize=8,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=6,
            fontName=table_font,
            leading=10
        )
        
        story.append(Paragraph(
            "─────────────────────────────────────────────────────────────────",
            dogrulama_divider_style
        ))
        
        story.append(Paragraph(
            ensure_unicode("<b>BELGENİN GEÇERLİLİĞİ VE DOĞRULAMA</b>"),
            dogrulama_title_style
        ))
        story.append(Spacer(1, 0.2*cm))
        
        story.append(Paragraph(
            ensure_unicode(
                "<b>Belge Bilgileri:</b><br/>"
                f"• Belge Referans No: {mutabakat_data['mutabakat_no']}<br/>"
                "• Bu belge elektronik ortamda oluşturulmuş olup, dijital imza ile korunmaktadır<br/>"
                "• Belgenin geçerliliği QR kod üzerinden doğrulanabilir"
            ),
            dogrulama_text_style
        ))
        
        story.append(Spacer(1, 0.2*cm))
        
        # Doğrulama ve destek bilgisi - şirket bilgilerinden al
        company_info = mutabakat_data.get('company_info', {})
        company_website = company_info.get('website', 'www.dinogida.com.tr')
        company_email = company_info.get('email', 'info@dinogida.com.tr')
        company_phone = company_info.get('phone', '0850 220 45 66')
        
        story.append(Paragraph(
            ensure_unicode(
                f"<b>Doğrulama ve Destek:</b><br/>"
                f"Belgenin geçerliliği {company_website} adresinden veya {company_email} "
                f"e-posta adresi üzerinden doğrulanabilir. Belge ile ilgili her türlü soru ve "
                f"destek talepleriniz için {company_phone} numaralı telefonu arayabilirsiniz."
            ),
            dogrulama_text_style
        ))
        
        story.append(Paragraph(
            "─────────────────────────────────────────────────────────────────",
            dogrulama_divider_style
        ))
        
        # PDF'i oluştur
        doc.build(story)
        
        # Buffer'ı başa sar
        self.buffer.seek(0)
        
        return self.buffer.getvalue()


# Kullanım fonksiyonu
def create_mutabakat_pdf(mutabakat, user, ip_info, action, red_nedeni=None, company=None):
    """
    Mutabakat PDF'i oluştur (Multi-Company)
    
    Args:
        mutabakat: Mutabakat objesi
        user: Kullanıcı objesi
        ip_info: IP bilgisi (dict - ISP bilgili) veya string (geriye dönük uyumluluk)
        action: 'ONAYLANDI' veya 'REDDEDİLDİ'
        red_nedeni: Red nedeni (opsiyonel)
        company: Company objesi (mutabakatin ait olduğu şirket - logo ve footer için)
    
    Returns:
        PDF bytes
    """
    generator = MutabakatPDFGenerator()
    
    # Bayi detayları (VKN bazlı mutabakat için)
    bayi_detaylari = []
    if hasattr(mutabakat, 'bayi_detaylari') and mutabakat.bayi_detaylari:
        for bayi in mutabakat.bayi_detaylari:
            bayi_detaylari.append({
                'bayi_kodu': bayi.bayi_kodu,
                'bayi_adi': bayi.bayi_adi,
                'bakiye': float(bayi.bakiye or 0)
            })
    
    # Gönderen ve alıcı şirket bilgileri (Company tablosundan)
    # Gönderen: mutabakat.sender'ın bağlı olduğu şirket
    sender_company_obj = mutabakat.sender.company if hasattr(mutabakat.sender, 'company') else None
    sender_company_name = sender_company_obj.full_company_name if sender_company_obj and sender_company_obj.full_company_name else (
        sender_company_obj.company_name if sender_company_obj else (
            mutabakat.sender.company_name or mutabakat.sender.full_name or mutabakat.sender.username
        )
    )
    
    # Alıcı: eğer müşteri/tedarikçi ise kendi company_name'i, değilse şirket bilgisi
    if mutabakat.receiver.role in [UserRole.MUSTERI, UserRole.TEDARIKCI]:
        receiver_company_name = mutabakat.receiver.company_name or mutabakat.receiver.full_name or mutabakat.receiver.username
    else:
        receiver_company_obj = mutabakat.receiver.company if hasattr(mutabakat.receiver, 'company') else None
        receiver_company_name = receiver_company_obj.full_company_name if receiver_company_obj and receiver_company_obj.full_company_name else (
            receiver_company_obj.company_name if receiver_company_obj else (
                mutabakat.receiver.company_name or mutabakat.receiver.full_name or mutabakat.receiver.username
            )
        )
    
    # Gönderen VKN (Şirket ise company.vkn, değilse user.vkn_tckn)
    sender_vkn = None
    if sender_company_obj and hasattr(sender_company_obj, 'vkn'):
        sender_vkn = sender_company_obj.vkn
    elif hasattr(mutabakat.sender, 'vkn_tckn'):
        sender_vkn = mutabakat.sender.vkn_tckn
    
    # Mutabakat verileri
    mutabakat_data = {
        'mutabakat_no': mutabakat.mutabakat_no,
        'sender_company': sender_company_name,
        'receiver_company': receiver_company_name,
        'sender_vkn': sender_vkn or '-',
        'receiver_vkn': mutabakat.receiver_vkn if hasattr(mutabakat, 'receiver_vkn') else (mutabakat.receiver.vkn_tckn if hasattr(mutabakat.receiver, 'vkn_tckn') else '-'),
        'sender_contact': mutabakat.sender.full_name or '-',
        'receiver_contact': mutabakat.receiver.full_name or '-',
        'sender_phone': mutabakat.sender.phone or '-',
        'receiver_phone': mutabakat.receiver.phone or '-',
        'sender_email': mutabakat.sender.email or '-',
        'receiver_email': mutabakat.receiver.email or '-',
        'donem_baslangic': mutabakat.donem_baslangic.strftime('%d.%m.%Y') if mutabakat.donem_baslangic else '-',
        'donem_bitis': mutabakat.donem_bitis.strftime('%d.%m.%Y') if mutabakat.donem_bitis else '-',
        'toplam_borc': float(mutabakat.toplam_borc or 0),
        'toplam_alacak': float(mutabakat.toplam_alacak or 0),
        'bakiye': float(mutabakat.bakiye or 0),
        'toplam_bayi_sayisi': mutabakat.toplam_bayi_sayisi if hasattr(mutabakat, 'toplam_bayi_sayisi') else 0,
        'bayi_detaylari': bayi_detaylari,
        'company_logo': company.logo_path if company and company.logo_path else None,  # Mutabakatin ait olduğu şirket logosu
        'company_info': {  # Footer için mutabakatin ait olduğu şirket bilgileri
            'website': company.website if company and company.website else 'www.dinogida.com.tr',
            'email': company.email if company and company.email else 'info@dinogida.com.tr',
            'phone': company.phone if company and company.phone else '0850 220 45 66',
            'full_name': company.full_company_name if company and company.full_company_name else (company.company_name if company else 'Dino Gıda San. Tic. Ltd. Şti.'),
            'address': company.address if company and company.address else ''
        }
    }
    
    # İşlem verileri
    action_data = {
        'action': action,
        'user_name': user.company_name or user.full_name or user.username,
        'timestamp': get_turkey_time().strftime('%d.%m.%Y %H:%M:%S'),
        'ip_address': ip_info if isinstance(ip_info, str) else ip_info.get('ip', 'Bilinmiyor'),
        'ip_info': ip_info,  # Tam ISP bilgisi (yasal delil için - dict veya string)
        'red_nedeni': red_nedeni
    }
    
    return generator.generate_mutabakat_pdf(mutabakat_data, action_data)

