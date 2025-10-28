# 🚀 E-Mutabakat Sistemi - Başlatma Kılavuzu

## 📋 Hazırlanan Script'ler

Sistemin rahat kullanımı için 4 adet Windows batch (.bat) dosyası hazırlanmıştır:

### 1️⃣ **start_all.bat** (ÖNERİLEN)
Her iki servisi ayrı pencerelerde başlatır. Her servisin loglarını kendi penceresinde görebilirsiniz.

**Kullanım:**
```cmd
start_all.bat
```

**Özellikler:**
- ✅ Backend ve Frontend ayrı CMD pencerelerinde açılır
- ✅ Her servisin logları kendi penceresinde görünür
- ✅ Servisleri durdurmak için ilgili pencereyi kapatmanız yeterli
- ✅ Otomatik port temizleme

**Pencereler:**
- **Ana Pencere:** Başlatma bilgileri
- **Backend Penceresi:** Python/FastAPI logları
- **Frontend Penceresi:** Vite/React logları

---

### 2️⃣ **start_all_single.bat**
Her iki servisi tek pencerede arka planda başlatır. Loglar dosyaya yazılır.

**Kullanım:**
```cmd
start_all_single.bat
```

**Özellikler:**
- ✅ Tek pencere, daha az karmaşa
- ✅ Loglar `logs/` dizinine kaydedilir
- ✅ Otomatik servis kontrolü (health check)
- ✅ Pencereyi kapatınca tüm servisler durur

**Log Dosyaları:**
```
logs/
├── backend_YYYYMMDD_HHMMSS.log
└── frontend_YYYYMMDD_HHMMSS.log
```

---

### 3️⃣ **stop_all.bat**
Çalışan tüm servisleri durdurur.

**Kullanım:**
```cmd
stop_all.bat
```

**Özellikler:**
- ✅ Tüm Python işlemlerini durdurur
- ✅ Tüm Node.js işlemlerini durdurur
- ✅ Port kullanımını kontrol eder
- ✅ Hangi işlemlerin durdurulduğunu gösterir

---

### 4️⃣ **restart_all.bat**
Servisleri yeniden başlatır.

**Kullanım:**
```cmd
restart_all.bat
```

**Özellikler:**
- ✅ Önce `stop_all.bat` çalıştırır
- ✅ Sonra `start_all.bat` çalıştırır
- ✅ Kod değişikliklerinden sonra kullanışlı

---

## 🔧 Manuel Başlatma

Script kullanmak istemiyorsanız manuel olarak da başlatabilirsiniz:

### Backend:
```cmd
cd C:\Users\Oguz\.cursor\Proje1
call venv\Scripts\activate.bat
python start_backend.py
```

### Frontend (Yeni Terminal):
```cmd
cd C:\Users\Oguz\.cursor\Proje1\frontend
npm run dev
```

---

## 🌐 Erişim Adresleri

Servisler başlatıldıktan sonra:

| Servis | URL | Açıklama |
|--------|-----|----------|
| **Frontend** | http://localhost:5173 | Ana uygulama arayüzü |
| **Backend API** | http://localhost:8000 | API servisi |
| **API Docs** | http://localhost:8000/docs | Swagger/OpenAPI dokümantasyonu |
| **Health Check** | http://localhost:8000/health | Servis sağlık kontrolü |

---

## ⚠️ Yaygın Sorunlar ve Çözümleri

### 1. Port Zaten Kullanımda
**Sorun:** `Port 8000 already in use` veya `Port 5173 already in use`

**Çözüm:**
```cmd
stop_all.bat
```
Eğer sorun devam ederse:
```cmd
netstat -ano | findstr ":8000 :5173"
taskkill /PID <PID_NUMARASI> /F
```

### 2. Python Bulunamadı
**Sorun:** `python is not recognized`

**Çözüm:**
```cmd
cd C:\Users\Oguz\.cursor\Proje1
call venv\Scripts\activate.bat
```

### 3. Node Bulunamadı
**Sorun:** `npm is not recognized`

**Çözüm:**
Node.js'in PATH'e eklendiğinden emin olun veya tam yolu kullanın.

### 4. Veritabanı Bağlantı Hatası
**Sorun:** `Connection to database failed`

**Çözüm:**
- `.env` dosyasındaki veritabanı bilgilerini kontrol edin
- SQL Server'ın çalıştığından emin olun
- Firewall ayarlarını kontrol edin

---

## 🔄 Geliştirme Süreci İçin Öneriler

### İlk Kurulum:
1. Veritabanı bağlantısını test edin
2. `start_all.bat` ile her iki servisi başlatın
3. http://localhost:5173 adresinden test edin

### Kod Değişikliği Sonrası:
- **Frontend değişikliği:** Otomatik hot-reload çalışır
- **Backend değişikliği:** `restart_all.bat` çalıştırın

### Hata Ayıklama:
- Ayrı pencere modu için: `start_all.bat` (logları direkt görmek için)
- Tek pencere modu için: `start_all_single.bat` (log dosyalarını inceleyin)

---

## 📝 Not

- Script'ler Windows için hazırlanmıştır
- PowerShell gerektirir (Windows 7+ varsayılan olarak yüklü)
- CMD'yi "Yönetici Olarak Çalıştır" yapmaya gerek yoktur
- Script'leri çift tıklayarak veya CMD'den çalıştırabilirsiniz

---

## 🎯 Hızlı Başlangıç

```cmd
REM Projeyi başlat
start_all.bat

REM Frontend: http://localhost:5173
REM Backend:  http://localhost:8000

REM Geliştirme yap...

REM Yeniden başlat
restart_all.bat

REM Durdur
stop_all.bat
```

---

## 📞 Destek

Sorun yaşarsanız:
1. `logs/` dizinindeki log dosyalarını inceleyin
2. `stop_all.bat` ile temiz bir başlangıç yapın
3. Manuel başlatma ile test edin
4. Veritabanı bağlantısını kontrol edin

---

**Son Güncelleme:** 25 Ekim 2025

