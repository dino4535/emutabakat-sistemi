# 🗄️ Veritabanı Kurulum Rehberi

## Adım 1: Veritabanını Oluşturun

SQL Server Management Studio (SSMS) veya Azure Data Studio'yu açın ve şu komutu çalıştırın:

```sql
CREATE DATABASE Mutabakat;
GO
```

✅ **Tamamlandı!** "Mutabakat" veritabanı oluşturuldu.

---

## Adım 2: Tabloları Oluşturun

İki yöntem var:

### Yöntem 1: Otomatik (Önerilen) ✨

Backend uygulaması ilk çalıştığında tabloları **otomatik olarak oluşturur**.

```bash
run_backend.bat
```

Backend başladığında konsola şunları göreceksiniz:
```
✓ Veritabanı bağlantısı başarılı!
✓ Tablolar başarıyla oluşturuldu!

Oluşturulan tablolar:
  - users
  - mutabakats
  - mutabakat_items
  - mutabakat_attachments
  - activity_logs
```

### Yöntem 2: Manuel SQL Script 📝

Eğer tabloları kendiniz oluşturmak isterseniz:

1. **SSMS'de** `create_tables.sql` dosyasını açın
2. Dosyayı çalıştırın (F5)
3. Sonuçlarda 5 tablonun oluşturulduğunu göreceksiniz

```sql
-- Dosya: create_tables.sql
USE Mutabakat;
-- Script otomatik olarak tüm tabloları oluşturur
```

---

## Adım 3: Tabloları Kontrol Edin

### SQL ile Kontrol:

```sql
USE Mutabakat;
GO

-- Tüm tabloları listele
SELECT name FROM sys.tables ORDER BY name;
GO

-- Tablo detayları
EXEC sp_help 'users';
EXEC sp_help 'mutabakats';
EXEC sp_help 'mutabakat_items';
GO
```

Veya `check_tables.sql` dosyasını çalıştırın:
```bash
# SSMS'de çalıştırın
check_tables.sql
```

### Beklenen Çıktı:

```
Tablo Adı              Satır Sayısı
---------------------- ------------
activity_logs          0
mutabakat_attachments  0
mutabakat_items        0
mutabakats             0
users                  0
```

---

## Oluşturulan Tablolar

### 1️⃣ **users** (Kullanıcılar)
Kullanıcı bilgileri ve kimlik doğrulama.

**Önemli Sütunlar:**
- `id` - Primary Key
- `email` - Unique, Kullanıcı emaili
- `username` - Unique, Kullanıcı adı
- `hashed_password` - Şifrelenmiş şifre
- `role` - Kullanıcı rolü (admin, muhasebe, musteri, tedarikci)
- `company_name` - Şirket adı
- `is_active` - Aktif mi?

### 2️⃣ **mutabakats** (Mutabakat Belgeleri)
Ana mutabakat belgeleri.

**Önemli Sütunlar:**
- `id` - Primary Key
- `mutabakat_no` - Unique, Mutabakat numarası (MUT-20250120...)
- `sender_id` - Gönderen kullanıcı (Foreign Key → users)
- `receiver_id` - Alıcı kullanıcı (Foreign Key → users)
- `donem_baslangic` / `donem_bitis` - Dönem bilgileri
- `toplam_borc` / `toplam_alacak` / `bakiye` - Mali toplamlar
- `durum` - Durum (taslak, gonderildi, onaylandi, reddedildi)
- `red_nedeni` - Red nedeni (varsa)

### 3️⃣ **mutabakat_items** (Mutabakat Kalemleri)
Mutabakat kalem detayları.

**Önemli Sütunlar:**
- `id` - Primary Key
- `mutabakat_id` - Bağlı mutabakat (Foreign Key → mutabakats)
- `tarih` - İşlem tarihi
- `belge_no` - Belge numarası
- `borc` / `alacak` - Borç ve alacak tutarları
- `aciklama` - Açıklama

### 4️⃣ **mutabakat_attachments** (Ekler)
Mutabakatlara eklenen dosyalar.

**Önemli Sütunlar:**
- `id` - Primary Key
- `mutabakat_id` - Bağlı mutabakat (Foreign Key → mutabakats)
- `file_name` / `file_path` - Dosya bilgileri
- `file_type` / `file_size` - Dosya detayları

### 5️⃣ **activity_logs** (Aktivite Logları)
Tüm sistem aktiviteleri.

**Önemli Sütunlar:**
- `id` - Primary Key
- `user_id` - İşlemi yapan kullanıcı (Foreign Key → users)
- `action` - Yapılan işlem (LOGIN, MUTABAKAT_OLUSTUR, vb.)
- `description` - Açıklama
- `ip_address` - IP adresi

---

## Veri İlişkileri (Foreign Keys)

```
users (1) ----< (∞) mutabakats (sender_id)
users (1) ----< (∞) mutabakats (receiver_id)
mutabakats (1) ----< (∞) mutabakat_items
mutabakats (1) ----< (∞) mutabakat_attachments
users (1) ----< (∞) activity_logs
```

---

## Test Verisi Ekleme (Opsiyonel)

Backend çalıştıktan sonra API üzerinden kayıt yapabilirsiniz, ancak test için manuel veri eklemek isterseniz:

```sql
-- Test kullanıcısı
INSERT INTO users (email, username, hashed_password, full_name, company_name, role)
VALUES 
    ('test@firma.com', 'testuser', '$2b$12$...', 'Test Kullanıcı', 'Test Firma A.Ş.', 'musteri');

-- Şifre hash'ini backend üzerinden almalısınız!
-- Frontend'den kayıt olun, bu daha güvenli.
```

---

## Sorun Giderme

### ❌ "Cannot open database 'Mutabakat'"
**Çözüm:** Veritabanını oluşturun:
```sql
CREATE DATABASE Mutabakat;
```

### ❌ "Login failed for user 'OGUZ'"
**Çözüm:** Kullanıcı haklarını kontrol edin:
```sql
USE Mutabakat;
CREATE USER [OGUZ] FOR LOGIN [OGUZ];
ALTER ROLE db_owner ADD MEMBER [OGUZ];
```

### ❌ "Table 'users' already exists"
**Çözüm:** Tablolar zaten oluşturulmuş. Kontrol edin:
```sql
SELECT name FROM sys.tables;
```

### ❌ Backend bağlanamıyor
**Kontrol listesi:**
1. SQL Server çalışıyor mu?
2. `.env` dosyasındaki bilgiler doğru mu?
3. ODBC Driver 17 yüklü mü?
4. Port 1433 açık mı?

---

## Veritabanı Yapılandırması

Backend `.env` dosyasından şu bilgileri kullanır:

```env
DB_SERVER=85.209.120.57
DB_NAME=Mutabakat
DB_USER=OGUZ
DB_PASSWORD=@1B9j9K045
DB_DRIVER=ODBC Driver 17 for SQL Server
```

---

## Başarılı Kurulum Kontrolü ✅

Tablolar başarıyla oluşturulduysa:

1. ✅ 5 tablo oluşturuldu
2. ✅ 13 index oluşturuldu
3. ✅ Foreign key ilişkileri kuruldu
4. ✅ Backend başarıyla bağlanıyor
5. ✅ http://localhost:8000/health → "healthy" döndürüyor

---

**Sonraki Adım:** Backend ve Frontend'i başlatın!

```bash
# Backend
run_backend.bat

# Frontend (yeni terminal)
run_frontend.bat
```

🚀 **Hazırsınız!** http://localhost:3000

