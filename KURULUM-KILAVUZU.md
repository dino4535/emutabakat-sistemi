# 🚀 E-MUTABAKAT SİSTEMİ - KURULUM KILAVUZU

## 📋 Genel Bakış

Bu kılavuz, E-Mutabakat sistemini Ubuntu 22.04 LTS sunucusuna Docker ile kurmak için gereken tüm adımları içerir.

---

## 🖥️ Sunucu Bilgileri

```
IP Adresi:   85.209.120.101
İşletim Sistemi: Ubuntu 22.04.5 LTS
Kullanıcı:   oguz
SSH Port:    22
```

---

## 📦 Hazırlık

### Windows Bilgisayarınızda Gerekli Programlar:

1. **SSH İstemcisi** (PowerShell/CMD yeterli)
2. **FileZilla** veya **WinSCP** (Dosya yükleme için)
   - FileZilla: https://filezilla-project.org/download.php?type=client
   - WinSCP: https://winscp.net/eng/download.php

---

## 🎯 KURULUM ADIMLARI

### ADIM 1: Kurulum Scriptini Sunucuya Yükle

#### 1.1. SSH ile Root Olarak Bağlan

Windows PowerShell veya CMD'de:

```powershell
ssh root@85.209.120.101
```

Şifre: `e341a63cc69a!diyo@`

#### 1.2. Kullanıcı "oguz" Oluştur

```bash
# Yeni kullanıcı oluştur
adduser oguz

# Şifre belirle (örnek: Oguz2024!Mutabakat)
# Diğer bilgileri boş bırak (Enter bas)

# Sudo yetkisi ver
usermod -aG sudo oguz

# Docker grubuna ekle (şimdilik boş ama ileride lazım)
groupadd docker 2>/dev/null || true
usermod -aG docker oguz

# Kontrol et
id oguz

# Root'tan çık
exit
```

#### 1.3. "oguz" Kullanıcısı ile Bağlan

```powershell
ssh oguz@85.209.120.101
```

oguz kullanıcısının şifresini gir.

---

### ADIM 2: Kurulum Scriptini İndir ve Çalıştır

#### 2.1. FileZilla/WinSCP ile Script Yükle

**FileZilla Bağlantı Bilgileri:**
```
Host:     sftp://85.209.120.101
Port:     22
Username: oguz
Password: oguz_kullanıcı_şifresi
```

**Yüklenecek Dosya:**
- `setup-server.sh` → `/home/oguz/` klasörüne yükle

#### 2.2. Scripti Çalıştırılabilir Yap

SSH'de (oguz kullanıcısı ile):

```bash
cd ~
chmod +x setup-server.sh
```

#### 2.3. Scripti Çalıştır

```bash
./setup-server.sh
```

Bu işlem **5-10 dakika** sürecek. Script şunları yapacak:
- ✅ Sistem güncellemeleri
- ✅ Docker kurulumu
- ✅ Firewall ayarları
- ✅ SQL Server ODBC driver
- ✅ Swap dosyası oluşturma
- ✅ Proje klasörlerini oluşturma
- ✅ Docker dosyalarını hazırlama

#### 2.4. Çıkış Yapıp Tekrar Gir (Docker Grubu İçin)

```bash
exit

# Tekrar bağlan
ssh oguz@85.209.120.101
```

---

### ADIM 3: Proje Dosyalarını Yükle

#### 3.1. FileZilla/WinSCP ile Dosya Yükleme

**Bağlantı Bilgileri:**
```
Host:     sftp://85.209.120.101
Port:     22
Username: oguz
Password: oguz_kullanıcı_şifresi
```

**Yüklenecek Klasörler ve Hedefler:**

| Windows Klasörü | Sunucu Hedefi |
|-----------------|---------------|
| `C:\Users\Oguz\.cursor\Proje1\backend\` | `/opt/mutabakat/musteri1/backend/` |
| `C:\Users\Oguz\.cursor\Proje1\frontend\` | `/opt/mutabakat/musteri1/frontend/` |
| `C:\Users\Oguz\.cursor\Proje1\certificates\dino_gida.p12` | `/opt/mutabakat/certificates/` |
| `C:\Users\Oguz\.cursor\Proje1\fonts\` | `/opt/mutabakat/musteri1/backend/fonts/` |

**⚠️ ÖNEMLİ - Yükleme Notları:**

❌ **YÜKLEME:**
- `backend/venv/` klasörünü yükleme
- `backend/__pycache__/` klasörlerini yükleme
- `frontend/node_modules/` klasörünü yükleme
- `frontend/dist/` klasörünü yükleme
- `.git/` klasörünü yükleme (opsiyonel)

✅ **YÜKLE:**
- Tüm `.py` dosyalarını
- `requirements.txt`
- Tüm `.jsx`, `.js`, `.css` dosyalarını
- `package.json`, `package-lock.json`
- `vite.config.js`, `index.html`
- `fonts/` klasörünü
- `certificates/dino_gida.p12` dosyasını

#### 3.2. Yükleme Kontrolü (SSH'de)

```bash
# Backend dosyaları
ls -lh /opt/mutabakat/musteri1/backend/
ls /opt/mutabakat/musteri1/backend/backend/

# Frontend dosyaları
ls -lh /opt/mutabakat/musteri1/frontend/
ls /opt/mutabakat/musteri1/frontend/src/

# Sertifika
ls -lh /opt/mutabakat/certificates/

# Fontlar
ls -lh /opt/mutabakat/musteri1/backend/fonts/
```

---

### ADIM 4: .env Dosyasını Oluştur

```bash
cd /opt/mutabakat/musteri1

# Template'i kopyala
cp .env.example .env

# Düzenle
nano .env
```

**.env Dosyası İçeriği:**

```env
# Database Configuration
DB_USER=sa
DB_PASSWORD=YourSQLServerPassword
SECRET_KEY=your-super-secret-random-key-min-32-characters-here

# Application
APP_NAME=E-Mutabakat
APP_ENV=production
```

**⚠️ Önemli:**
- `DB_PASSWORD`: SQL Server şifrenizi girin (85.209.120.57)
- `SECRET_KEY`: Rastgele 32+ karakterlik güçlü bir anahtar

**Kaydet:** `CTRL+X`, `Y`, `Enter`

---

### ADIM 5: Deployment Scriptini Yükle ve Çalıştır

#### 5.1. Deploy Scriptini Yükle

FileZilla/WinSCP ile:
- `deploy.sh` → `/opt/mutabakat/musteri1/` klasörüne yükle

#### 5.2. Scripti Çalıştırılabilir Yap ve Çalıştır

```bash
cd /opt/mutabakat/musteri1
chmod +x deploy.sh
./deploy.sh
```

Bu script:
- ✅ Docker image'larını build eder (5-10 dakika)
- ✅ Container'ları başlatır
- ✅ Sağlık kontrolü yapar
- ✅ Erişim bilgilerini gösterir

---

### ADIM 6: Test Et

#### 6.1. Container Durumunu Kontrol Et

```bash
docker ps
```

**Beklenen Çıktı:**
```
CONTAINER ID   IMAGE                    STATUS         PORTS
xxxxx          mutabakat_backend        Up 2 minutes   0.0.0.0:8000->8000/tcp
xxxxx          mutabakat_frontend       Up 2 minutes   0.0.0.0:80->80/tcp
```

#### 6.2. Backend Kontrolü

```bash
curl http://localhost:8000/health
```

**Beklenen Çıktı:**
```json
{"status":"healthy","database":"connected"}
```

#### 6.3. Frontend Kontrolü (Tarayıcıdan)

Windows bilgisayarınızdan tarayıcıda:

```
http://85.209.120.101
```

Login sayfasını görmelisiniz!

#### 6.4. API Dokümantasyonu

```
http://85.209.120.101:8000/docs
```

---

## 🔧 Sorun Giderme

### Logları İzle

```bash
cd /opt/mutabakat/musteri1

# Tüm loglar
docker compose logs -f

# Sadece backend
docker compose logs -f backend

# Sadece frontend
docker compose logs -f frontend
```

### Container'ı Yeniden Başlat

```bash
docker compose restart

# Sadece backend
docker compose restart backend
```

### Tamamen Sıfırdan Build

```bash
# Durdur ve kaldır
docker compose down

# Yeniden build et (cache kullanmadan)
docker compose build --no-cache

# Başlat
docker compose up -d
```

### Container İçine Gir (Debug)

```bash
# Backend
docker exec -it mutabakat_backend bash

# Frontend
docker exec -it mutabakat_frontend sh
```

---

## 🌐 Domain ve SSL Kurulumu (Opsiyonel)

### Domain Bağlandıktan Sonra:

#### 1. Nginx Reverse Proxy (Ana Sunucu)

```bash
sudo apt install nginx
sudo nano /etc/nginx/sites-available/mutabakat
```

```nginx
server {
    listen 80;
    server_name mutabakat.example.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/mutabakat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 2. Let's Encrypt SSL

```bash
# Certbot kur
sudo apt install certbot python3-certbot-nginx

# SSL al
sudo certbot --nginx -d mutabakat.example.com

# Otomatik yenileme testi
sudo certbot renew --dry-run
```

---

## 📊 Yedekleme

### Manuel Yedek

```bash
# Database yedek (SQL Server'dan)
# Bu işlem Windows SQL Server'da Management Studio ile yapılır

# PDF dosyaları yedek
cd /opt/mutabakat
tar -czf pdfs-backup-$(date +%Y%m%d).tar.gz pdfs/

# Sertifikalar yedek
tar -czf certificates-backup-$(date +%Y%m%d).tar.gz certificates/
```

### Otomatik Yedek (Cron)

```bash
crontab -e
```

```cron
# Her gün saat 02:00'da PDF yedekle
0 2 * * * cd /opt/mutabakat && tar -czf /backup/pdfs-$(date +\%Y\%m\%d).tar.gz pdfs/
```

---

## 🚀 Güncelleme

### Yeni Versiyon Deploy Etme

```bash
cd /opt/mutabakat/musteri1

# Dosyaları güncelle (FileZilla/WinSCP ile)

# Yeniden deploy et
./deploy.sh
```

---

## 📞 Destek

Sorun yaşarsanız:

1. Logları kontrol edin: `docker compose logs -f`
2. Container durumunu kontrol edin: `docker ps -a`
3. Sistem kaynaklarını kontrol edin: `htop`, `free -h`, `df -h`

---

## ✅ Kontrol Listesi

- [ ] `setup-server.sh` çalıştırıldı
- [ ] oguz kullanıcısı oluşturuldu ve docker grubuna eklendi
- [ ] Proje dosyaları yüklendi (backend, frontend, certificates, fonts)
- [ ] `.env` dosyası oluşturuldu ve yapılandırıldı
- [ ] `deploy.sh` çalıştırıldı
- [ ] Container'lar çalışıyor (`docker ps`)
- [ ] Backend health check başarılı
- [ ] Frontend tarayıcıdan erişilebilir
- [ ] Login sayfası görünüyor

---

## 🎉 Kurulum Tamamlandı!

Artık E-Mutabakat sisteminiz kullanıma hazır!

**Erişim:**
- Frontend: `http://85.209.120.101`
- Backend API: `http://85.209.120.101:8000`
- API Docs: `http://85.209.120.101:8000/docs`

**Varsayılan Giriş:**
- Kullanıcı: `admin`
- Şifre: (Veritabanınızdaki admin şifresi)

İyi çalışmalar! 🚀

