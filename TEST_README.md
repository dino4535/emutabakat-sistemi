# 🧪 E-Mutabakat Test Sistemi

Otomatik test sistemi kuruldu! Sisteminizin sağlığını ve işlevselliğini test edebilirsiniz.

## 📋 Test Kategorileri

### 1. **Smoke Tests** (Hızlı Sağlık Kontrolleri)
- Uygulama başlatma
- Health check
- API dokümantasyonu
- Temel endpoint'ler

### 2. **Unit Tests** (Birim Testleri)
- SMS log modeli
- PDF servisi
- Unicode dönüşümleri
- Yardımcı fonksiyonlar

### 3. **Integration Tests** (Entegrasyon Testleri)
- API endpoint'leri
- Veritabanı işlemleri
- SMS log kayıtları
- Token kullanımı

## 🚀 Testleri Çalıştırma

### Windows (PowerShell)

```powershell
# Tüm testleri çalıştır
python -m pytest backend/tests -v

# PowerShell script ile
.\run_tests.ps1

# Coverage ile
.\run_tests.ps1 --coverage

# Sadece smoke testler
python -m pytest backend/tests/test_smoke.py -v

# Sadece SMS log testleri
python -m pytest backend/tests/test_sms_logs.py -v
```

### Linux/Mac (Bash)

```bash
# Tüm testleri çalıştır
python -m pytest backend/tests -v

# Bash script ile
bash run_tests.sh

# Coverage ile
bash run_tests.sh --coverage
```

### Docker Container İçinde

```bash
# Backend container'ına gir
sudo docker exec -it emutabakat-backend bash

# Testleri çalıştır
cd /app
python -m pytest backend/tests -v
```

### Sunucuda (Production Check)

```bash
# Hızlı smoke test (sistem sağlığı)
sudo docker exec emutabakat-backend python -m pytest backend/tests/test_smoke.py -v

# Tüm testler
sudo docker exec emutabakat-backend python -m pytest backend/tests -v
```

## 📊 Test Sonuçları

Testler şunları kontrol eder:

✅ **Health Check**
- `/health` endpoint çalışıyor mu?
- Veritabanı bağlantısı var mı?

✅ **SMS Logs**
- SMS log modeli doğru çalışıyor mu?
- Token kullanımı kaydediliyor mu?
- IP/ISP bilgileri kaydediliyor mu?

✅ **PDF Generation**
- PDF oluşturulabiliyor mu?
- Unicode karakterler doğru mu?
- `corporate_divider` hatası var mı?

✅ **API Endpoints**
- Public endpoint'ler erişilebilir mi?
- Authentication çalışıyor mu?
- Error handling doğru mu?

## 🔧 Yeni Test Ekleme

### Örnek Test Dosyası

```python
# backend/tests/test_yeni_feature.py
import pytest
from backend.models import YeniModel

def test_yeni_feature(db):
    """Yeni özellik testi"""
    # Test kodunuz
    assert True
```

### Test Fixtures

Mevcut fixtures:
- `db`: Test veritabanı session'ı
- `client`: FastAPI test client
- `test_company`: Test şirketi
- `test_admin_user`: Test admin kullanıcısı
- `auth_headers`: Auth token ile header'lar

## 📈 CI/CD Entegrasyonu

GitHub Actions ile otomatik test:
- Her push'da testler çalışır
- Pull request'lerde testler zorunlu
- Coverage raporu oluşturulur

## 🐛 Sorun Giderme

### Testler çalışmıyor?

```powershell
# Windows PowerShell
# Dependencies kontrol et
pip install -r requirements.txt

# Pytest kurulu mu?
pip install pytest pytest-asyncio httpx

# Test klasörü var mı?
Get-ChildItem backend\tests\
```

```bash
# Linux/Mac
# Dependencies kontrol et
pip install -r requirements.txt

# Pytest kurulu mu?
pip install pytest pytest-asyncio httpx

# Test klasörü var mı?
ls backend/tests/
```

### Veritabanı hatası?

Testler SQLite in-memory kullanır (production DB'ye dokunmaz).

### PowerShell hatası?

Eğer `&&` veya `||` hatası alıyorsanız:
- PowerShell'de `.\run_tests.ps1` kullanın
- Veya doğrudan `python -m pytest backend/tests -v` komutunu çalıştırın

## 📝 Test Coverage

Coverage raporu oluşturmak için:

```powershell
# Windows
python -m pytest backend/tests --cov=backend --cov-report=html
Start-Process htmlcov\index.html  # HTML raporu aç
```

```bash
# Linux/Mac
python -m pytest backend/tests --cov=backend --cov-report=html
open htmlcov/index.html  # HTML raporu aç
```

## 🎯 Öneriler

1. **Her özellik eklediğinizde test yazın**
2. **Critical path'leri mutlaka test edin** (PDF, SMS, Onay)
3. **Smoke testleri her deploy öncesi çalıştırın**
4. **Coverage %80+ hedefleyin**

## 📞 Destek

Test sistemi hakkında sorularınız için:
- Test dosyalarını inceleyin: `backend/tests/`
- Pytest dokümantasyonu: https://docs.pytest.org/

---

**Not:** Testler production veritabanına dokunmaz. Güvenle çalıştırabilirsiniz! ✅
