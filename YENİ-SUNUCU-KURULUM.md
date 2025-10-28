# 🚀 YENİ SUNUCU - TEK SCRIPT İLE KURULUM

## 📋 Özet

Tek script ile:
- ✅ oguz kullanıcısı oluşturulur
- ✅ Docker kurulur
- ✅ Tüm sistem hazırlanır
- ✅ Klasör yapısı oluşturulur
- ✅ Dockerfile'lar düzeltilmiş halde hazırlanır

---

## 🎯 KURULUM ADIMLARI

### 1️⃣ Sunucuya Root ile Bağlan

```bash
ssh root@85.209.120.101
# Şifre: e341a63cc69a!diyo@
```

---

### 2️⃣ Kurulum Scriptini Yükle

**FileZilla/WinSCP ile:**
```
Dosya: kurulum-tamam.sh
Hedef: /root/
```

**Veya wget ile (daha hızlı):**
```bash
# Scripti indir (eğer bir URL'den sunabilirsen)
# wget https://... -O kurulum-tamam.sh
```

---

### 3️⃣ Scripti Çalıştır

```bash
# Çalıştırılabilir yap
chmod +x kurulum-tamam.sh

# Çalıştır!
bash kurulum-tamam.sh
```

**⏱️ Süre:** 10-15 dakika

**Göreceksin:**
```
╔═══════════════════════════════════════════════════════════════╗
║     E-MUTABAKAT SİSTEMİ - TAM OTOMATİK KURULUM               ║
║     Root ile çalıştırılmalıdır!                              ║
╚═══════════════════════════════════════════════════════════════╝

[1/12] Kullanıcı 'oguz' oluşturuluyor...
✓ Kullanıcı oluşturuldu!
  Kullanıcı: oguz
  Şifre: Oguz2024!Mutabakat

[2/12] Sistem güncellemeleri yapılıyor...
✓ Sistem güncellemeleri tamamlandı!

[3/12] Gerekli paketler kuruluyor...
...
```

---

### 4️⃣ Script Bitince - oguz ile Bağlan

```bash
# Root'tan çık
exit

# oguz ile bağlan
ssh oguz@85.209.120.101
# Şifre: Oguz2024!Mutabakat
```

---

### 5️⃣ Proje Dosyalarını Yükle

**FileZilla ile oguz kullanıcısına bağlan:**

```
Protocol:   SFTP
Host:       85.209.120.101
Port:       22
Username:   oguz
Password:   Oguz2024!Mutabakat
```

**Yüklenecek Dosyalar:**

| Windows | Sunucu |
|---------|--------|
| `C:\Users\Oguz\.cursor\Proje1\backend\` | `/opt/mutabakat/musteri1/backend/` |
| `C:\Users\Oguz\.cursor\Proje1\frontend\` | `/opt/mutabakat/musteri1/frontend/` |
| `C:\Users\Oguz\.cursor\Proje1\certificates\dino_gida.p12` | `/opt/mutabakat/certificates/` |

**⚠️ ÖNEMLİ:**
- Backend klasörünü tam yükle (`backend/backend/` dahil!)
- `node_modules`, `venv`, `__pycache__` yükleme!
- `frontend/dist/` yükleme!

---

### 6️⃣ .env Dosyasını Oluştur

```bash
cd /opt/mutabakat/musteri1

# Template'i kopyala
cp .env.example .env

# Düzenle
nano .env
```

**Değiştir:**
```env
DB_PASSWORD=YourSQLServerPassword
SECRET_KEY=dino-mutabakat-2024-prod-k8Hx9mP2vN5qR7wL3jT6yU4bF8eG1aZ0
```

**Kaydet:** `CTRL+X` → `Y` → `Enter`

---

### 7️⃣ Deploy Et!

```bash
cd /opt/mutabakat/musteri1
./deploy.sh
```

**⏱️ Süre:** 5-10 dakika (Docker build)

**Göreceksin:**
```
╔═══════════════════════════════════════════════════════════════╗
║     E-MUTABAKAT SİSTEMİ - DEPLOYMENT                         ║
╚═══════════════════════════════════════════════════════════════╝

[1/5] Ön kontroller...
✓ Ön kontroller başarılı!

[2/5] Eski container'lar durduruluyor...

[3/5] Docker image'ları build ediliyor...
Bu işlem 5-10 dakika sürebilir...
...

[5/5] Sağlık kontrolü...
✓ Backend çalışıyor!
✓ Frontend çalışıyor!

╔═══════════════════════════════════════════════════════════════╗
║           ✓ DEPLOYMENT TAMAMLANDI!                           ║
╚═══════════════════════════════════════════════════════════════╝

ERİŞİM BİLGİLERİ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 Frontend:     http://85.209.120.101
🔧 Backend API:  http://85.209.120.101:8000
📊 API Docs:     http://85.209.120.101:8000/docs
💚 Health:       http://85.209.120.101:8000/health
```

---

### 8️⃣ Test Et!

**Tarayıcıdan:**
```
http://85.209.120.101
```

**SSH'de:**
```bash
# Container durumu
docker ps

# Backend log
docker logs mutabakat_backend

# Frontend log
docker logs mutabakat_frontend

# Health check
curl http://localhost:8000/health
```

---

## 🎉 Tamamlandı!

Artık sistem hazır ve çalışıyor!

---

## 🔧 Sık Kullanılan Komutlar

```bash
# Container'ları göster
docker ps

# Logları izle
docker logs -f mutabakat_backend
docker logs -f mutabakat_frontend

# Container'ları yeniden başlat
cd /opt/mutabakat/musteri1
docker compose restart

# Container'ları durdur
docker compose down

# Yeniden deploy et
./deploy.sh
```

---

## 📋 Kontrol Listesi

- [ ] ✅ `kurulum-tamam.sh` çalıştırıldı (root)
- [ ] ✅ oguz kullanıcısı ile bağlanıldı
- [ ] ✅ Backend dosyaları yüklendi
- [ ] ✅ Frontend dosyaları yüklendi
- [ ] ✅ Sertifika dosyası yüklendi
- [ ] ✅ `.env` dosyası oluşturuldu
- [ ] ✅ `deploy.sh` çalıştırıldı
- [ ] ✅ Container'lar çalışıyor
- [ ] ✅ Frontend erişilebilir
- [ ] ✅ Backend health check başarılı

---

## 💡 Önemli Notlar

### Kullanıcı Şifresi
```
Kullanıcı: oguz
Şifre:     Oguz2024!Mutabakat
```

**⚠️ Script'te değiştirebilirsin:**
```bash
NEW_USER_PASSWORD="YeniŞifren"  # 8. satırda
```

### Docker Permission
Script oguz kullanıcısını docker grubuna otomatik ekliyor. İlk bağlantıda sorun olursa:
```bash
exit
ssh oguz@85.209.120.101
```

### Dockerfile'lar
Tüm bilinen hatalar düzeltilmiş:
- ✅ Frontend: `npm ci` (--only-production kaldırıldı)
- ✅ Backend: Modern apt-key yöntemi
- ✅ Backend: Doğru CMD satırı (`--app-dir backend`)

---

## 🆘 Sorun Giderme

### Script Hatası
```bash
# Log dosyasını kontrol et
cat /var/log/syslog | grep kurulum
```

### Docker Permission
```bash
# Manuel ekle
sudo usermod -aG docker oguz
exit
ssh oguz@85.209.120.101
```

### Container Restart Ediyor
```bash
# Logları kontrol et
docker logs mutabakat_backend
docker logs mutabakat_frontend

# .env dosyasını kontrol et
cat /opt/mutabakat/musteri1/.env
```

---

## 🚀 Hepsi Bu Kadar!

**Toplam Süre:** ~25-30 dakika
**Adım Sayısı:** 8 adım

İyi çalışmalar! 🎉

