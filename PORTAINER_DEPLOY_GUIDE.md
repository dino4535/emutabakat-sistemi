# 🚀 PORTAINER İLE DEPLOY REHBERİ

## 📋 Gereksinimler

### Sunucunuzda Kurulu Olması Gerekenler:
- ✅ Docker
- ✅ Docker Compose
- ✅ Portainer (85.209.120.101:9443) ✅
- ✅ SQL Server (85.209.120.57) ✅

---

## 🎯 ADIM ADIM KURULUM

### **ADIM 1: Dosyaları Sunucuya Yükleyin**

Tüm proje dosyalarını sunucuya yükleyin. Bunun için 3 yöntem:

#### **Yöntem A: Git ile (Önerilen)**
```bash
# Sunucuya SSH ile bağlanın
ssh root@85.209.120.101

# Proje dizinini oluşturun
mkdir -p /opt/emutabakat
cd /opt/emutabakat

# Git'ten çekin (eğer GitHub/GitLab'da ise)
git clone YOUR_REPO_URL .

# Veya yerel bilgisayardan rsync ile:
# rsync -avz -e ssh /path/to/Proje1/ root@85.209.120.101:/opt/emutabakat/
```

#### **Yöntem B: WinSCP veya FileZilla ile**
1. WinSCP/FileZilla'yı açın
2. 85.209.120.101'e bağlanın
3. Tüm proje klasörünü `/opt/emutabakat/` dizinine yükleyin

#### **Yöntem C: Portainer üzerinden (Küçük dosyalar için)**
Portainer'da "Stacks" → "Add Stack" → "Upload" ile docker-compose.yml yüklenebilir

---

### **ADIM 2: Environment Dosyasını Hazırlayın**

```bash
cd /opt/emutabakat

# .env.production dosyasını .env olarak kopyalayın
cp .env.production .env

# Dosyayı düzenleyin
nano .env
```

**Değiştirmeniz gereken değerler:**

```bash
# 1. SECRET_KEY üretin (rastgele 64 karakter)
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# 2. .env dosyasında değerleri güncelleyin:
DATABASE_URL=mssql+pyodbc://mutabakat_user:PASSWORD@85.209.120.57:1433/Mutabakat?driver=ODBC+Driver+17+for+SQL+Server
SECRET_KEY=<yukarıda-ürettiğiniz-key>
REDIS_PASSWORD=<güçlü-bir-şifre>

# 3. Email ayarları (opsiyonel)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**Dosya izinlerini kısıtlayın:**
```bash
chmod 600 .env
```

---

### **ADIM 3: Fontlar ve Sertifikaları Yükleyin**

```bash
# Fonts dizinini oluşturun ve fontları kopyalayın
mkdir -p /opt/emutabakat/fonts
# Yerel bilgisayardan fonts klasörünü kopyalayın

# Certificates dizinini oluşturun
mkdir -p /opt/emutabakat/certificates
# Dijital imza sertifikalarınızı buraya kopyalayın

# Gerekli diğer dizinler
mkdir -p /opt/emutabakat/uploads
mkdir -p /opt/emutabakat/pdfs
```

---

### **ADIM 4: Portainer'da Stack Oluşturun**

#### **4.1. Portainer'a Giriş Yapın**
1. Tarayıcıda https://85.209.120.101:9443 adresine gidin
2. Kullanıcı adı ve şifrenizle giriş yapın

#### **4.2. Stack Oluşturun**
1. Sol menüden **"Stacks"** seçeneğine tıklayın
2. **"+ Add stack"** butonuna tıklayın
3. Stack adı: **`emutabakat`**

#### **4.3. docker-compose.yml Yükleyin**

**Yöntem 1: Web editor ile (Önerilen)**
1. "Web editor" sekmesinde kalın
2. `/opt/emutabakat/docker-compose.yml` dosyasının içeriğini kopyalayın
3. Portainer'ın editörüne yapıştırın

**Yöntem 2: Upload ile**
1. "Upload" sekmesine tıklayın
2. `docker-compose.yml` dosyasını seçin
3. Upload edin

#### **4.4. Environment Variables Ekleyin**

"Advanced mode" toggle'ını açın ve `.env` dosyanızın içeriğini ekleyin:

```
DATABASE_URL=mssql+pyodbc://...
SECRET_KEY=your-secret-key
REDIS_PASSWORD=emutabakat2025
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
...
```

#### **4.5. Stack'i Deploy Edin**
1. **"Deploy the stack"** butonuna tıklayın
2. Portainer Docker image'larını indirecek ve konteynerları başlatacak
3. İlk deploy 5-10 dakika sürebilir (image download)

---

### **ADIM 5: Deployment'ı Kontrol Edin**

#### **5.1. Konteyner Durumlarını Kontrol Edin**
Portainer'da "Stacks" → "emutabakat" → Container list:

```
✅ emutabakat-redis         (healthy)
✅ emutabakat-backend       (healthy)
✅ emutabakat-celery-worker (running)
✅ emutabakat-celery-beat   (running)
✅ emutabakat-flower        (running)
✅ emutabakat-frontend      (healthy)
```

#### **5.2. Logları İnceleyin**
Her konteyner için "Logs" butonuna tıklayarak hataları kontrol edin:

```bash
# Backend logs
[OK] Veritabani baglantisi basarili!
[OK] Redis cache baglantisi basarili
INFO: Uvicorn running on http://0.0.0.0:8000

# Frontend logs
nginx: [emerg] bind() to 0.0.0.0:80 failed
```

#### **5.3. Health Check**
```bash
# Backend health
curl http://85.209.120.101/api/health

# Frontend health
curl http://85.209.120.101/
```

---

### **ADIM 6: DNS ve Firewall Ayarları**

#### **6.1. Firewall Portlarını Açın**
```bash
# HTTP
sudo ufw allow 80/tcp

# HTTPS (gelecek için)
sudo ufw allow 443/tcp

# Flower (opsiyonel, sadece admin IP'lerinden)
sudo ufw allow from YOUR_ADMIN_IP to any port 5555
```

#### **6.2. Domain Ayarları (Opsiyonel)**
Eğer domain kullanacaksanız:
```
A Record: emutabakat.com     → 85.209.120.101
A Record: www.emutabakat.com → 85.209.120.101
```

---

## 🔒 GÜVENLİK KONTROL LİSTESİ

- [ ] `.env` dosyası `chmod 600` ile korundu
- [ ] `SECRET_KEY` rastgele 64 karakterlik bir değer
- [ ] `REDIS_PASSWORD` güçlü bir şifre
- [ ] `FLOWER_PASSWORD` değiştirildi
- [ ] SQL Server şifresi güçlü
- [ ] Firewall aktif ve gerekli portlar açık
- [ ] Sadece gerekli portlar dışarıya açık (80, 443)
- [ ] SSH şifre yerine key authentication kullanıyor
- [ ] Root login devre dışı

---

## 🌐 ERİŞİM ADRESLERİ

Deployment sonrası erişim adresleri:

```
Frontend:         http://85.209.120.101
Backend API:      http://85.209.120.101/api
API Docs:         http://85.209.120.101/api/docs
Health Check:     http://85.209.120.101/api/health
Flower (Celery):  http://85.209.120.101:5555
Portainer:        https://85.209.120.101:9443
```

---

## 🔧 YAPILANDIRMA ÖNERİLERİ

### **Reverse Proxy (Nginx/Caddy) - Gelecek İçin**

Daha profesyonel bir kurulum için:
1. Ayrı bir Nginx konteyner ekleyin
2. SSL/TLS sertifikası (Let's Encrypt)
3. Rate limiting
4. Security headers

### **Monitoring**

Sistem izleme için:
- Flower: Celery task monitoring (http://85.209.120.101:5555)
- Portainer: Container stats
- Prometheus + Grafana (opsiyonel)

### **Backup**

```bash
# Database backup
# SQL Server'ınızda zaten backup mekanizmanız var

# Docker volumes backup
docker run --rm \
  -v emutabakat_redis_data:/data \
  -v /opt/backups:/backup \
  alpine tar czf /backup/redis-$(date +%Y%m%d).tar.gz /data
```

---

## 🆘 SORUN GİDERME

### **Problem: Backend başlamıyor**

**Çözüm 1: Database bağlantısı**
```bash
# Portainer'da backend container logs:
[ERROR] Database connection failed

# .env dosyasında DATABASE_URL'i kontrol edin
# SQL Server'ın erişilebilir olduğunu test edin:
docker exec -it emutabakat-backend python -c "
from sqlalchemy import create_engine
engine = create_engine('YOUR_DATABASE_URL')
conn = engine.connect()
print('OK')
"
```

**Çözüm 2: Missing dependencies**
```bash
# Backend container'a girin
docker exec -it emutabakat-backend bash

# Paketleri kontrol edin
pip list | grep fastapi
```

### **Problem: Redis bağlantı hatası**

```bash
# Redis container'ı kontrol edin
docker exec -it emutabakat-redis redis-cli

# Şifre ile bağlanın
auth emutabakat2025
ping
# Response: PONG
```

### **Problem: Frontend 502 Bad Gateway**

```bash
# Backend'in çalıştığını kontrol edin
curl http://backend:8000/health

# Nginx config'i kontrol edin
docker exec -it emutabakat-frontend cat /etc/nginx/conf.d/default.conf
```

### **Problem: ODBC Driver bulunamıyor**

Backend Dockerfile'a ekleyin:
```dockerfile
RUN apt-get update && apt-get install -y \
    curl apt-transport-https \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17
```

---

## 🔄 GÜNCELLEME SÜRECİ

Yeni versiyon deploy etmek için:

```bash
# 1. Yeni kodu sunucuya yükleyin (git pull veya rsync)
cd /opt/emutabakat
git pull

# 2. Portainer'da stack'i yeniden deploy edin
# Stacks → emutabakat → "Update the stack"

# VEYA terminal'den:
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 📊 PERFORMANS İYİLEŞTİRMELERİ

### **Docker Resource Limits**

docker-compose.yml'de her servis için:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### **Redis Memory Limit**
```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

---

## ✅ BAŞARILI DEPLOYMENT KONTROL LİSTESİ

- [ ] Tüm konteynerler "healthy" durumda
- [ ] Frontend http://85.209.120.101 adresinden erişilebiliyor
- [ ] Login ekranı açılıyor
- [ ] Giriş yapılabiliyor
- [ ] Dashboard yükleniyor
- [ ] Mutabakat oluşturulabiliyor
- [ ] PDF indirilebiliyor
- [ ] Email bildirimleri çalışıyor (SMTP yapılandırıldıysa)
- [ ] Celery taskları çalışıyor (Flower'dan kontrol)
- [ ] Redis cache çalışıyor

---

## 🎉 DEPLOYMENT TAMAMLANDI!

Sistem başarıyla deploy edildi! 🚀

**Sonraki Adımlar:**
1. SSL/TLS sertifikası ekleyin (Let's Encrypt)
2. Domain bağlayın
3. Monitoring kurun
4. Backup stratejisi oluşturun
5. Faz 2 (Güvenlik) özelliklerini ekleyin

---

**Sorularınız için:**
- Portainer Docs: https://docs.portainer.io
- Docker Compose: https://docs.docker.com/compose/
- FastAPI: https://fastapi.tiangolo.com

İyi çalışmalar! 🎊

