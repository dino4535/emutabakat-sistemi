# 🔧 Login Sorunu Çözümü

## Sorun
Backend'de **passlib ve bcrypt** çakışması var. Login yaparken hata alıyorsunuz.

## ✅ Çözüm Adımları

### 1️⃣ Backend'i Durdurun
Çalışan backend penceresinde **CTRL+C** yapın veya pencereyi kapatın.

### 2️⃣ Bcrypt'i Yeniden Yükleyin
```bash
cd C:\Users\Oguz\.cursor\Proje1
venv\Scripts\pip.exe uninstall bcrypt -y
venv\Scripts\pip.exe install bcrypt==4.0.1
```

### 3️⃣ Backend'i Yeniden Başlatın
```bash
run_backend.bat
```

### 4️⃣ Frontend'i Başlatın
```bash
run_frontend.bat
```

### 5️⃣ Giriş Yapın
- **URL:** http://localhost:3000
- **Kullanıcı:** `admin`
- **Şifre:** `admin123`

---

## 🚀 Hızlı Çözüm (Tek Komut)

Backend'i durdurduktan sonra bu scripti çalıştırın:

```batch
cd C:\Users\Oguz\.cursor\Proje1
venv\Scripts\pip.exe uninstall passlib bcrypt -y
venv\Scripts\pip.exe install bcrypt==4.0.1
```

Sonra tekrar başlatın:
```batch
run_backend.bat
```

---

## ✅ Test Kullanıcıları

| Kullanıcı | Şifre | Rol |
|-----------|-------|-----|
| admin | admin123 | Admin |
| muhasebe1 | muhasebe123 | Muhasebe |
| musteri1 | musteri123 | Müşteri |
| tedarikci1 | tedarikci123 | Tedarikçi |

---

## 📝 Yapılan Değişiklikler

✅ `backend/auth.py` - Passlib yerine saf bcrypt kullanıyor
✅ `requirements.txt` - Passlib kaldırıldı, bcrypt eklendi
✅ Tüm kullanıcı şifreleri bcrypt ile hash'lendi
✅ Login sistemi tamamen bcrypt ile çalışıyor

---

**Backend'i durdurduktan sonra bcrypt'i yeniden yükleyin ve başlatın!**

