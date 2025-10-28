# ⚡ HIZLI BAŞLANGIÇ

## 🎯 5 Adımda Kurulum

### 1️⃣ Root ile Bağlan ve Kullanıcı Oluştur

```bash
# Windows PowerShell/CMD:
ssh root@85.209.120.101
# Şifre: e341a63cc69a!diyo@

# Sunucuda:
adduser oguz
usermod -aG sudo oguz
groupadd docker 2>/dev/null || true
usermod -aG docker oguz
exit

# oguz ile bağlan:
ssh oguz@85.209.120.101
```

---

### 2️⃣ Kurulum Scriptini Yükle ve Çalıştır

**FileZilla/WinSCP ile:**
- `setup-server.sh` → `/home/oguz/` yükle

**SSH'de:**
```bash
cd ~
chmod +x setup-server.sh
./setup-server.sh

# İşlem bitince çıkış yap ve tekrar gir (Docker grubu için)
exit
ssh oguz@85.209.120.101
```

⏱️ **Süre:** 5-10 dakika

---

### 3️⃣ Proje Dosyalarını Yükle

**FileZilla/WinSCP ile yükle:**

| Windows | Sunucu |
|---------|--------|
| `C:\Users\Oguz\.cursor\Proje1\backend\` | `/opt/mutabakat/musteri1/backend/` |
| `C:\Users\Oguz\.cursor\Proje1\frontend\` | `/opt/mutabakat/musteri1/frontend/` |
| `C:\Users\Oguz\.cursor\Proje1\certificates\dino_gida.p12` | `/opt/mutabakat/certificates/` |
| `C:\Users\Oguz\.cursor\Proje1\fonts\` | `/opt/mutabakat/musteri1/backend/fonts/` |

❌ **node_modules, venv, __pycache__ yükleme!**

---

### 4️⃣ .env Dosyasını Yapılandır

```bash
cd /opt/mutabakat/musteri1
cp .env.example .env
nano .env
```

**Düzenle:**
```env
DB_USER=sa
DB_PASSWORD=YourSQLServerPassword  # <-- Buraya SQL şifrenizi girin
SECRET_KEY=random-32-char-secret   # <-- Güçlü rastgele anahtar
```

**Kaydet:** `CTRL+X`, `Y`, `Enter`

---

### 5️⃣ Deploy Et!

**FileZilla/WinSCP ile:**
- `deploy.sh` → `/opt/mutabakat/musteri1/` yükle

**SSH'de:**
```bash
cd /opt/mutabakat/musteri1
chmod +x deploy.sh
./deploy.sh
```

⏱️ **Süre:** 5-10 dakika (Docker build)

---

## ✅ Test Et

**Tarayıcıdan:**
```
http://85.209.120.101
```

**API Kontrol:**
```bash
curl http://85.209.120.101:8000/health
```

---

## 🔧 Sık Kullanılan Komutlar

```bash
# Container durumu
docker ps

# Logları izle
docker compose logs -f

# Yeniden başlat
docker compose restart

# Durdur
docker compose down

# Yeniden build
docker compose build --no-cache
docker compose up -d
```

---

## 📱 Erişim Bilgileri

| Servis | URL |
|--------|-----|
| **Frontend** | http://85.209.120.101 |
| **Backend API** | http://85.209.120.101:8000 |
| **API Docs** | http://85.209.120.101:8000/docs |
| **Health Check** | http://85.209.120.101:8000/health |

---

## 🆘 Sorun mu Var?

```bash
# Logları kontrol et
docker compose logs -f backend
docker compose logs -f frontend

# Container'ları yeniden başlat
docker compose restart

# Tamamen sıfırdan
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## 📚 Detaylı Bilgi

Daha fazla bilgi için: **[KURULUM-KILAVUZU.md](./KURULUM-KILAVUZU.md)**

---

🚀 **Hepsi bu kadar! İyi çalışmalar!**

