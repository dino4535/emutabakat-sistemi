# 🚀 Audit Log Sistemi - Deployment Kılavuzu

## 📦 Yapılan Değişiklikler (3 Commit)

### Commit 1: Backend Audit Log Sistemi
- ✅ `backend/models.py` - AuditLog ve AuditLogAction eklendi
- ✅ `backend/routers/audit_logs.py` - API endpoint'leri
- ✅ `backend/utils/audit_logger.py` - Helper fonksiyonlar
- ✅ `backend/utils/create_audit_log_table.py` - Python migration script
- ✅ `backend/utils/create_audit_log_table.sql` - SQL migration script
- ✅ `backend/routers/auth.py` - Login audit log entegrasyonu
- ✅ `backend/routers/mutabakat.py` - Import eklendi
- ✅ `backend/main.py` - Router eklendi
- ✅ `frontend/src/pages/AuditLogs.jsx` - Tam sayfa component
- ✅ `AUDIT_LOG_README.md` - Detaylı dokümantasyon

### Commit 2: Frontend Routing ve Menü
- ✅ `frontend/src/App.jsx` - `/audit-logs` route eklendi
- ✅ `frontend/src/components/Layout.jsx` - Menüye "Audit Logs" eklendi

### Commit 3: Dashboard Widget
- ✅ `frontend/src/components/RecentAuditLogs.jsx` - Widget component
- ✅ `frontend/src/pages/Dashboard.jsx` - Widget entegrasyonu

---

## 🎯 Deployment Adımları

### 1. Git Pull ve Build
```bash
cd /opt/emutabakat

# Git'ten çek (3 commit)
sudo git pull

# Servisleri durdur
sudo docker compose down

# Yeniden build et (frontend ve backend)
sudo docker compose build --no-cache

# Başlat
sudo docker compose up -d

# Logları izle
sudo docker logs -f --tail=100 emutabakat-backend
```

**Beklenen çıktı:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### 2. Audit Log Tablosunu Oluştur

```bash
# Python script ile
sudo docker exec emutabakat-backend python backend/utils/create_audit_log_table.py
```

**Beklenen çıktı:**
```
============================================================
AUDIT LOG TABLO OLUŞTURMA
============================================================
🔍 Audit Log tablosu kontrol ediliyor...
🔨 Audit Log tablosu oluşturuluyor...
✅ 'audit_logs' tablosu başarıyla oluşturuldu!
   - 23 sütun
   - 8 index
   - 0 kayıt
🎉 Audit Log sistemi hazır!
```

---

### 3. Tablo Kontrolü

```bash
# Tablo var mı?
sudo docker exec emutabakat-backend python -c "
from backend.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
count = db.execute(text('SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = \"audit_logs\"')).scalar()
print(f'Audit Logs Tablosu: {\"✅ VAR\" if count > 0 else \"❌ YOK\"}')
db.close()
"

# Kayıt sayısı
sudo docker exec emutabakat-backend python -c "
from backend.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
count = db.execute(text('SELECT COUNT(*) FROM audit_logs')).scalar()
print(f'Toplam Log Kayıt: {count}')
db.close()
"
```

---

### 4. İlk Test - Login

```bash
# Admin ile login yap
curl -X POST "http://127.0.0.1:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=dino_gida_admin&password=Dino45??*123D"
```

**Sonra logları kontrol et:**
```bash
sudo docker exec emutabakat-backend python -c "
from backend.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
logs = db.execute(text('SELECT TOP 5 action, username, status, created_at FROM audit_logs ORDER BY created_at DESC')).fetchall()
print('\n=== SON 5 AUDİT LOG ===')
for log in logs:
    print(f'{log.created_at} | {log.action:20s} | {log.username:20s} | {log.status}')
db.close()
"
```

**Beklenen çıktı:**
```
=== SON 5 AUDİT LOG ===
2025-11-03 22:30:15 | login                | dino_gida_admin      | success
```

---

### 5. Frontend Kontrolü

#### A. Dashboard Widget (Admin)
```
URL: https://mutabakat.dinogida.com.tr/dashboard
Kullanıcı: admin veya company_admin
Beklenen: Dashboard'ın altında "📋 Son Sistem Logları" widget'ı
```

#### B. Audit Logs Sayfası
```
URL: https://mutabakat.dinogida.com.tr/audit-logs
Kullanıcı: admin veya company_admin
Beklenen: 
  - İstatistik kartları (Toplam, Bugün, Hatalı, Kullanıcılar)
  - Filtre alanları
  - Tablo görünümü
  - CSV İndir butonu
  - Sayfalama
```

#### C. Menü Kontrolü
```
Sidebar Menü → Yönetim Bölümü → "Audit Logs" linki
```

---

### 6. API Test

```bash
# Token al
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/api/auth/login" \
  -d "username=dino_gida_admin&password=Dino45??*123D" | \
  jq -r '.access_token')

# Audit logları listele
curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/api/audit-logs/?page=1&page_size=10" | jq

# İstatistikler
curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/api/audit-logs/stats" | jq

# CSV export
curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/api/audit-logs/export/csv" -o audit_logs.csv
```

---

## 🔍 Sorun Giderme

### Sorun 1: Tablo Oluşturulamadı
```bash
# Manuel SQL ile oluştur
sudo docker exec -i emutabakat-backend python -c "
from backend.database import engine
from sqlalchemy import text

with open('backend/utils/create_audit_log_table.sql', 'r') as f:
    sql = f.read()
    
with engine.connect() as conn:
    conn.execute(text(sql))
    print('✅ SQL script çalıştırıldı')
"
```

### Sorun 2: Frontend 403 Hatası
```
Sebep: Kullanıcı admin değil
Çözüm: Admin veya company_admin hesabı ile giriş yapın
```

### Sorun 3: Widget Görünmüyor
```bash
# Browser console'u kontrol et (F12)
# Şu hatayı arıyoruz: "403 Forbidden"

# Kullanıcı rolünü kontrol et
sudo docker exec emutabakat-backend python -c "
from backend.database import SessionLocal
from backend.models import User
db = SessionLocal()
user = db.query(User).filter(User.username == 'dino_gida_admin').first()
print(f'Kullanıcı: {user.username}')
print(f'Rol: {user.role}')
print(f'Admin mi?: {user.role in [\"admin\", \"company_admin\"]}')
db.close()
"
```

### Sorun 4: Log Kaydedilmiyor
```bash
# Backend loglarını kontrol et
sudo docker logs --tail=100 emutabakat-backend | grep -i "audit"

# Manuel log ekle (test)
sudo docker exec emutabakat-backend python -c "
from backend.database import SessionLocal
from backend.utils.audit_logger import create_audit_log
from backend.models import AuditLogAction
db = SessionLocal()
create_audit_log(
    db=db,
    action=AuditLogAction.API_ACCESS,
    action_description='Test log kaydı',
    status='success'
)
print('✅ Test log eklendi')
db.close()
"
```

---

## 📊 Başarı Kriterleri

✅ **Backend**
- [ ] `audit_logs` tablosu oluşturuldu
- [ ] Login işlemi log kaydediliyor
- [ ] API endpoint'leri çalışıyor (`/api/audit-logs/`)
- [ ] İstatistikler getiriliyor

✅ **Frontend**
- [ ] Dashboard'da widget görünüyor (admin için)
- [ ] `/audit-logs` sayfası açılıyor
- [ ] Menüde "Audit Logs" linki var
- [ ] Filtreleme çalışıyor
- [ ] CSV export çalışıyor

✅ **Entegrasyon**
- [ ] Login yapınca log oluşuyor
- [ ] Başarısız login denemeleri loglanıyor
- [ ] IP ve ISP bilgileri kaydediliyor
- [ ] Tarih ve saat doğru (Türkiye saati)

---

## 🎉 Deployment Tamamlandı!

Tüm kontroller başarılı ise:

1. **Production kullanıma hazır**
2. **Yasal gereklilikleri karşılıyor**
3. **Güvenlik izleme aktif**
4. **Denetim kayıtları tutulıyor**

---

## 📞 Destek

Sorun yaşarsanız:
1. Backend loglarını kontrol edin
2. Frontend console'u kontrol edin (F12)
3. Veritabanı bağlantısını test edin
4. Bu dokümandaki sorun giderme adımlarını uygulayın

**Deployment başarılar! 🚀**

