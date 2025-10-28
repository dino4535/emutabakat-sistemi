#!/usr/bin/env python3
"""
GoldSMS API Test Scripti
"""
import requests
import json

# GoldSMS Bilgileri
USERNAME = "dinogıda45"
PASSWORD = "Dino45??*123D"
SENDER = "DiNO GIDA"
TEST_PHONE = "905557604389"

def test_credit():
    """Kredi kontrolü"""
    print("=" * 60)
    print("1. KREDİ KONTROLÜ TESTİ")
    print("=" * 60)
    
    url = "http://apiv3.goldmesaj.net/api/kredi/get"
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, ensure_ascii=False)}\n")
        
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30,
            verify=False
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}\n")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'ok':
                credit = int(result.get('result', 0))
                print(f"[OK] BASARILI! Kredi: {credit} SMS\n")
                return True, credit
            else:
                print(f"[HATA] Response: {result}\n")
                return False, 0
        else:
            print(f"[HATA] HTTP HATASI! Status: {response.status_code}\n")
            return False, 0
            
    except requests.exceptions.Timeout:
        print("[HATA] TIMEOUT! API'ye erisilemedi (30 saniye asildi)\n")
        return False, 0
    except Exception as e:
        print(f"[HATA] EXCEPTION! Hata: {e}\n")
        return False, 0

def test_send_sms():
    """SMS gönderme testi"""
    print("=" * 60)
    print("2. SMS GÖNDERME TESTİ")
    print("=" * 60)
    
    url = "http://apiv3.goldmesaj.net/api/sendSMS"
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "sdate": "",
        "vperiod": "23",
        "gate": 0,
        "message": {
            "sender": SENDER,
            "text": "TEST SMS - E-Mutabakat Sistemi",
            "utf8": "1",
            "gsm": [TEST_PHONE]
        }
    }
    
    try:
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, ensure_ascii=False)}\n")
        
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30,
            verify=False
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}\n")
        
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] BASARILI! Response: {result}\n")
            return True
        else:
            print(f"[HATA] HTTP HATASI! Status: {response.status_code}\n")
            return False
            
    except requests.exceptions.Timeout:
        print("[HATA] TIMEOUT! API'ye erisilemedi (30 saniye asildi)\n")
        return False
    except Exception as e:
        print(f"[HATA] EXCEPTION! Hata: {e}\n")
        return False

def test_network():
    """Network bağlantı testi"""
    print("=" * 60)
    print("0. NETWORK BAĞLANTI TESTİ")
    print("=" * 60)
    
    import socket
    
    # DNS çözümleme
    try:
        ip = socket.gethostbyname("apiv3.goldmesaj.net")
        print(f"[OK] DNS cozumleme basarili: apiv3.goldmesaj.net -> {ip}")
    except Exception as e:
        print(f"[HATA] DNS cozumleme hatasi: {e}")
        return False
    
    # Port 80 erişim testi
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, 80))
        sock.close()
        
        if result == 0:
            print(f"[OK] Port 80 erisilebilir\n")
            return True
        else:
            print(f"[HATA] Port 80 erisilemedi (error code: {result})\n")
            return False
    except Exception as e:
        print(f"[HATA] Port kontrolu hatasi: {e}\n")
        return False

if __name__ == "__main__":
    print("\n")
    print("GOLDSMS API TEST BASLIYOR...")
    print("\n")
    
    # 0. Network testi
    network_ok = test_network()
    
    if not network_ok:
        print("[UYARI] Network baglantisi yok! Firewall kurallarini kontrol edin.")
        exit(1)
    
    # 1. Kredi kontrolü
    credit_ok, credit = test_credit()
    
    if not credit_ok:
        print("[UYARI] Kredi kontrolu basarisiz! Kullanici adi/sifre dogru mu?")
        exit(1)
    
    if credit < 1:
        print(f"[UYARI] Kredi yetersiz! Mevcut: {credit} SMS")
        exit(1)
    
    # 2. SMS gönderme testi
    sms_ok = test_send_sms()
    
    if not sms_ok:
        print("[UYARI] SMS gonderimi basarisiz!")
        exit(1)
    
    print("=" * 60)
    print("[BASARILI] TUM TESTLER BASARILI!")
    print("=" * 60)
    print("\nBu durumda backend'deki SMS sistemi de çalışacaktır.")
    print("Sunucuda kodu güncelleyip backend'i rebuild edin:\n")
    print("  cd /opt/emutabakat")
    print("  git pull origin main")
    print("  docker-compose down")
    print("  docker-compose up -d --build backend celery-worker")
    print("  docker-compose logs -f backend")
    print("\n")

