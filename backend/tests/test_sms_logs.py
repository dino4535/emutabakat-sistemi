"""
SMS Verification Logs Testleri
"""
import pytest
from datetime import datetime
from backend.models import SMSVerificationLog, Mutabakat, MutabakatDurumu, User
from backend.database import SessionLocal


def test_sms_log_model_creation(db, test_company):
    """SMS log modeli oluşturma testi"""
    # Önce bir mutabakat oluştur
    sender = User(
        company_id=test_company.id,
        vkn_tckn="11111111111",
        username="sender",
        hashed_password="hash",
        role="admin",
        is_active=True
    )
    receiver = User(
        company_id=test_company.id,
        vkn_tckn="22222222222",
        username="receiver",
        hashed_password="hash",
        role="musteri",
        is_active=True
    )
    db.add(sender)
    db.add(receiver)
    db.commit()
    
    mutabakat = Mutabakat(
        company_id=test_company.id,
        mutabakat_no="MUT-20251103-TEST",
        sender_id=sender.id,
        receiver_id=receiver.id,
        receiver_vkn="22222222222",
        donem_baslangic=datetime.now(),
        donem_bitis=datetime.now(),
        durum=MutabakatDurumu.GONDERILDI,
        approval_token="test_token_123"
    )
    db.add(mutabakat)
    db.commit()
    
    # SMS log oluştur
    sms_log = SMSVerificationLog(
        mutabakat_id=mutabakat.id,
        approval_token="test_token_123",
        phone="905551234567",
        receiver_name="Test Müşteri",
        sms_message="Test SMS mesajı",
        ip_address="192.168.1.1",
        isp="Test ISP",
        city="Istanbul",
        country="Turkey",
        sms_status="sent",
        sms_provider="goldsms"
    )
    db.add(sms_log)
    db.commit()
    db.refresh(sms_log)
    
    assert sms_log.id is not None
    assert sms_log.mutabakat_id == mutabakat.id
    assert sms_log.phone == "905551234567"
    assert sms_log.token_used == False
    assert sms_log.sms_status == "sent"


def test_sms_log_token_usage(db, test_company):
    """SMS log token kullanımı testi"""
    # Yukarıdaki test'teki gibi mutabakat ve log oluştur
    sender = User(
        company_id=test_company.id,
        vkn_tckn="11111111111",
        username="sender",
        hashed_password="hash",
        role="admin",
        is_active=True
    )
    receiver = User(
        company_id=test_company.id,
        vkn_tckn="22222222222",
        username="receiver",
        hashed_password="hash",
        role="musteri",
        is_active=True
    )
    db.add(sender)
    db.add(receiver)
    db.commit()
    
    mutabakat = Mutabakat(
        company_id=test_company.id,
        mutabakat_no="MUT-20251103-TEST2",
        sender_id=sender.id,
        receiver_id=receiver.id,
        receiver_vkn="22222222222",
        donem_baslangic=datetime.now(),
        donem_bitis=datetime.now(),
        durum=MutabakatDurumu.GONDERILDI,
        approval_token="test_token_456"
    )
    db.add(mutabakat)
    db.commit()
    
    sms_log = SMSVerificationLog(
        mutabakat_id=mutabakat.id,
        approval_token="test_token_456",
        phone="905551234567",
        receiver_name="Test Müşteri",
        sms_message="Test SMS",
        ip_address="192.168.1.1",
        sms_status="sent"
    )
    db.add(sms_log)
    db.commit()
    
    # Token kullanıldı olarak işaretle
    sms_log.token_used = True
    sms_log.token_used_at = datetime.now()
    db.commit()
    db.refresh(sms_log)
    
    assert sms_log.token_used == True
    assert sms_log.token_used_at is not None

