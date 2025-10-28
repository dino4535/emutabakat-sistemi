# ⚡ PORTAINER HIZLI BAŞLANGIÇ

## 🎯 3 ADIMDA DEPLOY

### **ADIM 1: Dosyaları Sunucuya Yükleyin (5 dakika)**

#### Windows'tan WinSCP ile:
```
1. WinSCP'yi açın
2. Host: 85.209.120.101
3. Username: root (veya sudo yetkili kullanıcı)
4. Bağlanın
5. Tüm proje klasörünü /opt/emutabakat/ dizinine yükleyin
```

#### Linux/Mac'ten rsync ile:
```bash
rsync -avz -e ssh C:\Users\Oguz\.cursor\Proje1/ root@85.209.120.101:/opt/emutabakat/
```

---

### **ADIM 2: Environment Dosyasını Hazırlayın (3 dakika)**

Sunucuya SSH ile bağlanın:
```bash
ssh root@85.209.120.101
cd /opt/emutabakat

# SECRET_KEY üretin
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# .env dosyası oluşturun
nano .env
```

.env dosyasına yapıştırın:
```bash
DATABASE_URL=mssql+pyodbc://mutabakat_user:PASSWORD@85.209.120.57:1433/Mutabakat?driver=ODBC+Driver+17+for+SQL+Server
SECRET_KEY=<yukarıda-üretilen-key>
REDIS_PASSWORD=emutabakat2025
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@emutabakat.com
FLOWER_USER=admin
FLOWER_PASSWORD=admin2025
```

**CTRL+X → Y → Enter** ile kaydedin

```bash
# Dosya izinlerini kısıtlayın
chmod 600 .env

# Gerekli dizinleri oluşturun
mkdir -p fonts certificates uploads pdfs
```

---

### **ADIM 3: Portainer'da Deploy Edin (2 dakika)**

1. **Portainer'a gidin:** https://85.209.120.101:9443
2. **Stacks** → **+ Add stack**
3. **Name:** `emutabakat`
4. **Build method:** Web editor
5. **docker-compose.yml** dosyasının içeriğini kopyalayıp yapıştırın
6. **Environment variables** bölümünde:
   - "Load variables from .env file" seçeneğini işaretleyin
   - **VEYA** `.env` dosyanızın içeriğini "Advanced mode" ile yapıştırın
7. **Deploy the stack** butonuna tıklayın

---

## ✅ KONTROL

5-10 dakika sonra:

```
✅ Frontend:  http://85.209.120.101
✅ Backend:   http://85.209.120.101/api/docs
✅ Flower:    http://85.209.120.101:5555
```

---

## 🆘 SORUN GİDERME

### Backend başlamıyor?
```bash
# Logları kontrol edin
docker logs emutabakat-backend

# En yaygın sorun: Database bağlantısı
# .env dosyasında DATABASE_URL'i kontrol edin
```

### Frontend 502 hatası?
```bash
# Backend'in hazır olmasını bekleyin (1-2 dakika)
docker ps  # Tüm konteynerların çalıştığını kontrol edin
```

### Redis bağlantı hatası?
```bash
# Redis'in başladığını kontrol edin
docker logs emutabakat-redis
```

---

## 📞 YARDIM

Detaylı dokümantasyon için: **PORTAINER_DEPLOY_GUIDE.md**

---

**Başarılar! 🚀**

