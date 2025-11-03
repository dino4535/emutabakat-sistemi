"""
PDF Servisi Testleri
"""
import pytest
from backend.utils.pdf_service import MutabakatPDFGenerator, ensure_unicode
from datetime import datetime


def test_ensure_unicode():
    """Unicode dönüşümü testi"""
    assert ensure_unicode("Test") == "Test"
    assert ensure_unicode("Türkçe") == "Türkçe"
    assert ensure_unicode(None) == "-"
    assert ensure_unicode(b"bytes") == "bytes"


def test_pdf_generator_init():
    """PDF generator başlatma testi"""
    generator = MutabakatPDFGenerator()
    assert generator.buffer is not None
    assert generator.pagesize is not None


def test_pdf_generation():
    """PDF oluşturma testi (basit)"""
    generator = MutabakatPDFGenerator()
    
    mutabakat_data = {
        'mutabakat_no': 'MUT-TEST-001',
        'sender_company': 'Test Şirketi',
        'receiver_company': 'Test Müşteri',
        'sender_vkn': '1234567890',
        'receiver_vkn': '0987654321',
        'toplam_borc': 1000.0,
        'toplam_alacak': 500.0,
        'bakiye': 500.0,
        'donem_baslangic': '01.01.2025',
        'donem_bitis': '31.01.2025',
        'bayi_detaylari': [],
        'company_logo': None,
        'company_info': {
            'website': 'www.test.com',
            'email': 'test@test.com',
            'phone': '0850 123 45 67'
        }
    }
    
    action_data = {
        'action': 'ONAYLANDI',
        'user_name': 'Test User',
        'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
        'ip_address': '192.168.1.1',
        'ip_info': {
            'isp': 'Test ISP',
            'city': 'Istanbul'
        }
    }
    
    try:
        pdf_bytes = generator.generate_mutabakat_pdf(mutabakat_data, action_data)
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')  # PDF dosyası başlangıcı
    except Exception as e:
        pytest.fail(f"PDF oluşturma hatası: {e}")

