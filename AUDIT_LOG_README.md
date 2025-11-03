# 📋 Audit Log Sistemi - Kullanım Kılavuzu

## 🎯 Genel Bakış

Audit Log sistemi, e-mutabakat sisteminde gerçekleşen **tüm kritik işlemleri** kayıt altına alır. Bu sistem:

- ✅ **Yasal Uyumluluk**: TTK, TBK ve KVKK gerekliliklerini karşılar
- ✅ **Güvenlik**: Tüm kullanıcı aktivitelerini izler
- ✅ **Denetim**: Sistem değişikliklerini takip eder
- ✅ **Sorun Giderme**: Hata ve performans analizi sağlar

---

## 📊 Loglanan İşlem Türleri

### 1. **Kimlik Doğrulama**
- `LOGIN`: Başarılı kullanıcı girişi
- `LOGIN_FAILED`: Başarısız giriş denemesi
- `LOGOUT`: Kullanıcı çıkışı
- `PASSWORD_CHANGE`: Şifre değiştirme

### 2. **Mutabakat İşlemleri**
- `MUTABAKAT_CREATE`: Mutabakat oluşturma
- `MUTABAKAT_UPDATE`: Mutabakat güncelleme
- `MUTABAKAT_DELETE`: Mutabakat silme
- `MUTABAKAT_SEND`: Mutabakat gönderme
- `MUTABAKAT_APPROVE`: Mutabakat onaylama
- `MUTABAKAT_REJECT`: Mutabakat reddetme
- `MUTABAKAT_CANCEL`: Mutabakat iptal
- `MUTABAKAT_VIEW`: Mutabakat görüntüleme
- `MUTABAKAT_DOWNLOAD_PDF`: PDF indirme

### 3. **Kullanıcı Yönetimi**
- `USER_CREATE`: Yeni kullanıcı oluşturma
- `USER_UPDATE`: Kullanıcı güncelleme
- `USER_DELETE`: Kullanıcı silme
- `USER_ACTIVATE`: Kullanıcı aktifleştirme
- `USER_DEACTIVATE`: Kullanıcı pasifleştirme

### 4. **Bayi/Müşteri Yönetimi**
- `BAYI_CREATE`: Bayi oluşturma
- `BAYI_UPDATE`: Bayi güncelleme
- `BAYI_DELETE`: Bayi silme
- `BAYI_IMPORT`: Toplu bayi import

### 5. **KVKK İşlemleri**
- `KVKK_CONSENT_GIVEN`: KVKK onayı verme
- `KVKK_CONSENT_WITHDRAWN`: KVKK onayı geri çekme
- `KVKK_DATA_EXPORT`: Kişisel veri export
- `KVKK_DATA_DELETE`: Kişisel veri silme

### 6. **Güvenlik**
- `UNAUTHORIZED_ACCESS`: Yetkisiz erişim denemesi
- `SUSPICIOUS_ACTIVITY`: Şüpheli aktivite

---

## 🚀 Kurulum

### 1. Veritabanı Tablosu Oluşturma

#### Yöntem A: Python Script ile
```bash
# Sunucuda
cd /opt/emutabakat
sudo docker exec emutabakat-backend python backend/utils/create_audit_log_table.py
```

#### Yöntem B: SQL Script ile
```bash
# SQL dosyasını çalıştır
sudo docker exec emutabakat-backend python -c "
from backend.database import engine
with open('backend/utils/create_audit_log_table.sql', 'r') as f:
    engine.execute(f.read())
"
```

#### Yöntem C: SQLAlchemy ile (Otomatik)
```python
# backend/main.py'de zaten tanımlı
from backend.models import AuditLog
# init_db() çağrıldığında otomatik oluşturulur
```

### 2. Tablo Oluşturuldu mu Kontrol Et
```bash
sudo docker exec emutabakat-backend python -c "
from backend.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
count = db.execute(text('SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = \'audit_logs\'')).scalar()
print(f'Audit Logs Tablosu: {\"✅ Var\" if count > 0 else \"❌ Yok\"}')
db.close()
"
```

---

## 💻 Kullanım Örnekleri

### 1. Login İşlemini Loglama
```python
from backend.utils.audit_logger import log_login_attempt

# Başarılı login
log_login_attempt(
    db=db,
    username="admin",
    success=True,
    ip_address="176.88.200.22",
    user_agent="Mozilla/5.0...",
    user=user,
    ip_info={
        "ip": "176.88.200.22",
        "isp": "Superonline",
        "city": "Istanbul",
        "country": "Turkey"
    }
)

# Başarısız login
log_login_attempt(
    db=db,
    username="hacker",
    success=False,
    ip_address="1.2.3.4",
    user_agent="BadBot/1.0",
    error_message="Şifre hatalı"
)
```

### 2. Mutabakat İşlemini Loglama
```python
from backend.utils.audit_logger import log_mutabakat_action
from backend.models import AuditLogAction

# Mutabakat oluşturma
log_mutabakat_action(
    db=db,
    action=AuditLogAction.MUTABAKAT_CREATE,
    mutabakat=mutabakat,
    user=current_user,
    description=f"Mutabakat oluşturuldu: {mutabakat.mutabakat_no}",
    new_values={"bakiye": mutabakat.bakiye},
    ip_info=ip_info,
    request=request
)

# Mutabakat onaylama
log_mutabakat_action(
    db=db,
    action=AuditLogAction.MUTABAKAT_APPROVE,
    mutabakat=mutabakat,
    user=current_user,
    description=f"Mutabakat onaylandı: {mutabakat.mutabakat_no}",
    old_values={"durum": "gonderildi"},
    new_values={"durum": "onaylandi"}
)
```

### 3. Manuel Log Kaydı (Genel)
```python
from backend.utils.audit_logger import create_audit_log
from backend.models import AuditLogAction

create_audit_log(
    db=db,
    action=AuditLogAction.REPORT_GENERATE,
    user=current_user,
    action_description="Aylık mutabakat raporu oluşturuldu",
    status="success",
    target_model="Report",
    target_id=report.id,
    request=request,
    duration_ms=1250,
    ip_info=ip_info
)
```

### 4. Hatalı İşlemi Loglama
```python
try:
    # Kritik işlem
    dangerous_operation()
except Exception as e:
    create_audit_log(
        db=db,
        action=AuditLogAction.API_ERROR,
        user=current_user,
        action_description="Kritik işlem başarısız",
        status="error",
        error_message=str(e),
        error_traceback=traceback.format_exc(),
        request=request
    )
    raise
```

---

## 🔍 Logları Görüntüleme

### 1. Frontend (Web Arayüzü)
```
https://mutabakat.dinogida.com.tr/audit-logs
```

- **Filtreleme**: Kullanıcı, tarih, işlem türü, durum
- **Arama**: Genel arama (kullanıcı, açıklama, IP)
- **Export**: CSV formatında indirme
- **İstatistikler**: Toplam log, bugünkü loglar, başarısız işlemler

### 2. API ile Sorgulama
```bash
# Tüm logları listele
curl -H "Authorization: Bearer $TOKEN" \
  "https://mutabakat.dinogida.com.tr/api/audit-logs/?page=1&page_size=50"

# Başarısız login denemelerini listele
curl -H "Authorization: Bearer $TOKEN" \
  "https://mutabakat.dinogida.com.tr/api/audit-logs/?action=login_failed&status=failed"

# Belirli bir kullanıcının işlemlerini listele
curl -H "Authorization: Bearer $TOKEN" \
  "https://mutabakat.dinogida.com.tr/api/audit-logs/?username=dino_gida_admin"

# İstatistikleri getir
curl -H "Authorization: Bearer $TOKEN" \
  "https://mutabakat.dinogida.com.tr/api/audit-logs/stats"

# CSV export
curl -H "Authorization: Bearer $TOKEN" \
  "https://mutabakat.dinogida.com.tr/api/audit-logs/export/csv" \
  -o audit_logs.csv
```

### 3. Veritabanından Direkt Sorgulama
```sql
-- Son 100 log kaydı
SELECT TOP 100 
    created_at,
    action,
    status,
    username,
    company_name,
    ip_address,
    action_description
FROM audit_logs
ORDER BY created_at DESC;

-- Başarısız login denemeleri (son 24 saat)
SELECT 
    username,
    ip_address,
    isp,
    city,
    error_message,
    created_at
FROM audit_logs
WHERE action = 'login_failed'
  AND created_at >= DATEADD(HOUR, -24, GETDATE())
ORDER BY created_at DESC;

-- Kullanıcı bazlı işlem sayıları
SELECT 
    username,
    COUNT(*) as total_actions,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
FROM audit_logs
WHERE created_at >= DATEADD(DAY, -7, GETDATE())
GROUP BY username
ORDER BY total_actions DESC;

-- Şüpheli IP adresleri (çok fazla başarısız deneme)
SELECT 
    ip_address,
    isp,
    city,
    country,
    COUNT(*) as failed_attempts
FROM audit_logs
WHERE action = 'login_failed'
  AND created_at >= DATEADD(HOUR, -1, GETDATE())
GROUP BY ip_address, isp, city, country
HAVING COUNT(*) > 5
ORDER BY failed_attempts DESC;
```

---

## 📊 Performans ve Optimizasyon

### Index'ler
Aşağıdaki index'ler otomatik oluşturulur:
- `IX_audit_logs_action` - İşlem türüne göre arama
- `IX_audit_logs_user_id` - Kullanıcıya göre arama
- `IX_audit_logs_company_id` - Şirkete göre arama
- `IX_audit_logs_created_at` - Tarihe göre sıralama
- `IX_audit_logs_username` - Kullanıcı adına göre arama
- `IX_audit_logs_ip_address` - IP adresine göre arama
- `IX_audit_logs_status` - Duruma göre filtreleme
- `IX_audit_logs_target_id` - Hedef kayda göre arama

### Veri Saklama Politikası
```sql
-- 1 yıldan eski logları arşivle/sil
DELETE FROM audit_logs
WHERE created_at < DATEADD(YEAR, -1, GETDATE());

-- Veya arşiv tablosuna taşı
INSERT INTO audit_logs_archive
SELECT * FROM audit_logs
WHERE created_at < DATEADD(YEAR, -1, GETDATE());
```

---

## 🔒 Güvenlik ve Yetkilendirme

### Kimin Erişimi Var?
- **Sistem Admini**: Tüm logları görebilir
- **Şirket Admini**: Sadece kendi şirketinin loglarını görebilir
- **Normal Kullanıcılar**: Erişim YOK

### API Yetkilendirme
```python
# backend/routers/audit_logs.py
if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
    raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
```

---

## 🧪 Test

### Manuel Test
```bash
# 1. Login yap ve audit log kontrol et
curl -X POST "http://localhost:8000/api/auth/login" \
  -d "username=admin&password=123456"

# 2. Audit logları kontrol et
sudo docker exec emutabakat-backend python -c "
from backend.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
logs = db.execute(text('SELECT TOP 5 action, username, created_at FROM audit_logs ORDER BY created_at DESC')).fetchall()
for log in logs:
    print(f'{log.created_at} | {log.action} | {log.username}')
db.close()
"
```

---

## 📈 Yasal Gereklilikler

Audit log sistemi aşağıdaki yasal gereklilikleri karşılar:

### 1. TTK (Türk Ticaret Kanunu)
- Madde 82: Ticari defterlerin tutulması
- Madde 88: Elektronik ortamda defter tutma

### 2. KVKK (Kişisel Verilerin Korunması Kanunu)
- Madde 12: Veri işleme faaliyetlerinin kayıt altına alınması
- Madde 13: Veri güvenliğinin sağlanması

### 3. Elektronik İmza Kanunu
- Madde 5: Elektronik kayıtların delil niteliği

---

## 🎉 Özet

✅ **Model Oluşturuldu**: `AuditLog` ve `AuditLogAction`  
✅ **API Endpoint'leri**: `/api/audit-logs/` (list, stats, export)  
✅ **Helper Fonksiyonlar**: `log_login_attempt`, `log_mutabakat_action`, `create_audit_log`  
✅ **Frontend Arayüzü**: React component (`AuditLogs.jsx`)  
✅ **Otomatik Loglama**: Login, mutabakat işlemleri  
✅ **Filtreleme ve Arama**: Kullanıcı, tarih, işlem türü  
✅ **CSV Export**: Raporlama için  

---

## 📞 Destek

Sorunlarınız için:
1. Backend loglarını kontrol edin: `sudo docker logs emutabakat-backend`
2. Veritabanı bağlantısını test edin
3. API endpoint'lerini test edin: `curl http://localhost:8000/api/audit-logs/actions/list`

🚀 **Audit Log sistemi hazır ve çalışıyor!**

