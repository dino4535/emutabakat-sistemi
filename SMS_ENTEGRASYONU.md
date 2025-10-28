# 📱 GoldSMS API Entegrasyonu

## Genel Bakış

E-Mutabakat sistemine **GoldSMS** API entegrasyonu yapılmıştır. Mutabakat süreçlerinde ilgili kişilere otomatik SMS bildirimleri gönderilir.

## SMS Gönderim Senaryoları

### 1. 📤 Mutabakat Gönderildiğinde

**Kime:** Müşteri/Tedarikçi (Alıcı)  
**Ne Zaman:** Mutabakat "Gönderildi" durumuna geçtiğinde

**SMS İçeriği:**
```
Sayin [Müşteri Adı],
Mutabakat No: MUT-20251020143020-A1B2
Tutar: 50,000.00 TL
Detaylar icin sisteme giris yapiniz.
- DiNO GIDA
```

### 2. ✅ Mutabakat Onaylandığında

**Kime:** Firma (Gönderen - Muhasebe/Planlama)  
**Ne Zaman:** Müşteri mutabakatı onayladığında

**SMS İçeriği:**
```
Mutabakat onaylandi!
Musteri: ABC Şirketi
Mutabakat No: MUT-20251020143020-A1B2
- DiNO GIDA
```

### 3. ❌ Mutabakat Reddedildiğinde

**Kime:** Firma (Gönderen - Muhasebe/Planlama)  
**Ne Zaman:** Müşteri mutabakatı reddettiğinde

**SMS İçeriği:**
```
Mutabakat reddedildi!
Musteri: ABC Şirketi
Mutabakat No: MUT-20251020143020-A1B2
Neden: Bakiye uyuşmuyor
- DiNO GIDA
```

## API Bilgileri

### GoldSMS Credentials

```env
GOLDSMS_USERNAME=dinogıda45
GOLDSMS_PASSWORD=Dino45??*123D
GOLDSMS_ORIGINATOR=DiNO GIDA
```

### API Endpoint

```
https://api.goldsms.com.tr/send/get
```

### Parametreler

| Parametre | Değer | Açıklama |
|-----------|-------|----------|
| `username` | dinogıda45 | GoldSMS kullanıcı adı |
| `password` | Dino45??*123D | GoldSMS şifre |
| `originator` | DiNO GIDA | Gönderici adı (Alfa Numeric) |
| `message` | SMS metni | Gönderilecek mesaj |
| `phones` | 905551234567 | Alıcı telefon numarası (90 ile başlamalı) |
| `encoding` | TR | Türkçe karakter desteği |

## Telefon Numarası Formatı

Sistem, telefon numaralarını otomatik olarak formatlar:

| Girilen Format | Çıktı Format |
|----------------|--------------|
| +905551234567 | 905551234567 |
| 05551234567 | 905551234567 |
| 5551234567 | 905551234567 |
| 0 (555) 123 45 67 | 905551234567 |

✅ **Doğru Format:** `905551234567` (90 + 10 rakam = 12 rakam)

## Hata Yönetimi

### SMS Gönderim Hatası

SMS gönderimi başarısız olsa bile mutabakat işlemi devam eder. Hatalar:
- ✅ Veritabanına loglanır
- ✅ Log dosyasına kaydedilir
- ❌ İşlemi durdurmaz

### Geçersiz Telefon Numarası

Eğer kullanıcının telefon numarası:
- ❌ Boş ise
- ❌ Geçersiz format ise
- ❌ 12 rakamdan farklı ise

SMS gönderilmez ve hata loglanır.

## Kod Yapısı

### `backend/sms.py`

```python
class GoldSMS:
    - send_sms(): Temel SMS gönderme
    - send_mutabakat_notification(): Mutabakat bildirimi
    - send_mutabakat_approved(): Onay bildirimi
    - send_mutabakat_rejected(): Red bildirimi
    - format_phone(): Telefon formatla
```

### Kullanım Örneği

```python
from backend.sms import sms_service

# Mutabakat bildirimi gönder
sms_service.send_mutabakat_notification(
    phone="05551234567",
    customer_name="ABC Şirketi",
    mutabakat_no="MUT-20251020143020-A1B2",
    amount=50000.00
)
```

## Test

### Manuel Test

1. Profil sayfasından telefon numaranızı ekleyin
2. Bir mutabakat oluşturun ve gönderin
3. SMS almanız gerekir

### Log Kontrolü

```bash
# Log dosyasını kontrol et
tail -f logs/app_20251020.log | grep SMS
```

**Başarılı SMS:**
```
[INFO] SMS başarıyla gönderildi: 905551234567, Mesaj ID: 123456
```

**Başarısız SMS:**
```
[ERROR] SMS gönderimi başarısız: Geçersiz telefon numarası
```

## API Limitleri

| Özellik | Değer |
|---------|-------|
| Mesaj Uzunluğu | Max 160 karakter (Türkçe: ~70 karakter) |
| Timeout | 10 saniye |
| Rate Limit | GoldSMS tarafından belirlenir |

## Güvenlik

- ✅ API credentials `.env` dosyasında saklanır
- ✅ Hassas bilgiler loglara yazılmaz
- ✅ SSL/TLS ile güvenli bağlantı
- ✅ Telefon numaraları formatlanır ve doğrulanır

## Maliyet

SMS maliyeti GoldSMS paketi ve kullanıma göre değişir. Detaylı bilgi için GoldSMS ile iletişime geçin.

## Sorun Giderme

### SMS Gitmiyor

1. **Telefon numarasını kontrol edin:**
   - Profil sayfasından doğru formatta girildiğinden emin olun
   - Format: +90 (5XX) XXX XX XX

2. **API credentials kontrol edin:**
   - `.env` dosyasında doğru bilgiler olduğundan emin olun

3. **Log dosyasını kontrol edin:**
   ```bash
   logs/app_20251020.log
   ```

4. **GoldSMS bakiyesini kontrol edin:**
   - GoldSMS hesabınızda yeterli bakiye olduğundan emin olun

### Hata Mesajları

| Hata | Çözüm |
|------|-------|
| `Geçersiz telefon numarası` | Telefonu doğru formatta girin |
| `SMS API zaman aşımı` | İnternet bağlantısını kontrol edin |
| `SMS gönderimi başarısız` | GoldSMS bakiyesini kontrol edin |

## Destek

Sorun yaşarsanız:
- 📧 GoldSMS Destek: support@goldsms.com.tr
- 📞 GoldSMS Tel: 0850 XXX XX XX

## Referanslar

- [GoldSMS API Dokümantasyonu](https://github.com/alirizaoztetik/ci-goldsms/blob/master/GoldSms.php)
- [GoldSMS Web Panel](https://www.goldsms.com.tr)

