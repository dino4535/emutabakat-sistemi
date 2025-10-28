# 📄 DİJİTAL İMZA DOĞRULAMA SİSTEMİ

## ⚖️ Mahkeme ve Yasal Otoriteler İçin Rehber

### 🎯 Amaç
Dino Gıda E-Mutabakat Sistemi tarafından oluşturulan PDF mutabakat belgelerinin orijinalliğini ve değiştirilmediğini matematiksel olarak kanıtlamak.

---

## 📋 Sistemin Nasıl Çalıştığı

### 1️⃣ **Dijital İmza Oluşturma**

PDF belgesi oluşturulurken, aşağıdaki veriler bir araya getirilerek **SHA-256 hash algoritması** ile şifrelenir:

```
Mutabakat No + Gönderen Şirket + Alıcı Şirket + Toplam Borç + Toplam Alacak + Durum + Tarih
```

**Örnek:**
```
MUT-20251020230253-I4MU
+ Dino Gıda San. Tic. Ltd. Şti.
+ XYZ San. Tic. A.S.
+ 900000.00
+ 0.00
+ ONAYLANDI
+ 20.10.2025 23:05:32
```

**Sonuç (SHA-256 Hash):**
```
0432dca0be20ae0e124c9dc3a2aef39f8516d1267af184476a4d96b4b40abc8
```

Bu hash, belgenin **dijital parmak izi**dir. Belgede tek bir karakter bile değişirse, hash tamamen farklı olur.

---

### 2️⃣ **Doğrulama Yöntemleri**

#### **Yöntem A: API Üzerinden Doğrulama (Önerilen)**

**Endpoint:**
```
POST https://api.dinogida.com.tr/api/verify/mutabakat
```

**Request Body (JSON):**
```json
{
  "mutabakat_no": "MUT-20251020230253-I4MU",
  "dijital_imza": "0432dca0be20ae0e124c9dc3a2aef39f8516d1267af184476a4d96b4b40abc8"
}
```

**Başarılı Yanıt (200 OK):**
```json
{
  "gecerli": true,
  "mesaj": "✓ Dijital imza GEÇERLİ. Bu belge Dino Gıda E-Mutabakat Sistemi tarafından oluşturulmuş ve değiştirilmemiştir.",
  "mutabakat_no": "MUT-20251020230253-I4MU",
  "durum": "Onaylandı",
  "sender_company": "Dino Gıda San. Tic. Ltd. Şti.",
  "receiver_company": "XYZ San. Tic. A.S.",
  "toplam_borc": 900000.00,
  "toplam_alacak": 0.00,
  "bakiye": -900000.00,
  "onay_tarihi": "20.10.2025 23:05:32"
}
```

**Geçersiz Yanıt (Belge Değiştirilmiş):**
```json
{
  "gecerli": false,
  "mesaj": "✗ Dijital imza GEÇERSİZ! Bu belge değiştirilmiş veya sahte olabilir.",
  "mutabakat_no": "MUT-20251020230253-I4MU"
}
```

---

#### **Yöntem B: cURL ile Test (Terminal)**

```bash
curl -X POST "https://api.dinogida.com.tr/api/verify/mutabakat" \
  -H "Content-Type: application/json" \
  -d '{
    "mutabakat_no": "MUT-20251020230253-I4MU",
    "dijital_imza": "0432dca0be20ae0e124c9dc3a2aef39f8516d1267af184476a4d96b4b40abc8"
  }'
```

---

#### **Yöntem C: Postman ile Test**

1. **Yeni Request Oluşturun:**
   - Method: `POST`
   - URL: `https://api.dinogida.com.tr/api/verify/mutabakat`

2. **Headers:**
   ```
   Content-Type: application/json
   ```

3. **Body (raw JSON):**
   ```json
   {
     "mutabakat_no": "MUT-20251020230253-I4MU",
     "dijital_imza": "0432dca0be20ae0e124c9dc3a2aef39f8516d1267af184476a4d96b4b40abc8"
   }
   ```

4. **Send** butonuna tıklayın.

---

### 3️⃣ **Basit Durum Sorgulama**

Sadece mutabakat durumunu sorgulamak için:

**Endpoint:**
```
GET https://api.dinogida.com.tr/api/verify/status/MUT-20251020230253-I4MU
```

**Yanıt:**
```json
{
  "mutabakat_no": "MUT-20251020230253-I4MU",
  "durum": "onaylandi",
  "sender": "Dino Gıda San. Tic. Ltd. Şti.",
  "receiver": "XYZ San. Tic. A.S.",
  "created_at": "20.10.2025 23:05:32",
  "onay_tarihi": "20.10.2025 23:05:32"
}
```

---

## 🔐 Güvenlik Özellikleri

### **1. Gerçek IP Adresi Kaydı**
- PDF'de görünen IP adresi, kullanıcının gerçek ISP (İnternet Servis Sağlayıcı) IP adresidir.
- Localhost (127.0.0.1) değil, public IP adresi kullanılır.
- IP adresi, işlemi kimin yaptığının coğrafi kanıtıdır.

### **2. Değiştirilemez Hash**
- SHA-256 algoritması tek yönlüdür (geri döndürülemez).
- Belgede tek bir noktalama işareti bile değiştirilirse, hash tamamen farklı olur.
- Hash çarpışması olasılığı astronomik olarak düşüktür (2^256 = ~10^77).

### **3. Zaman Damgası**
- Her işlem UTC+3 (Türkiye) saatiyle kaydedilir.
- Tarih formatı: `DD.MM.YYYY HH:MM:SS`
- Belge oluşturma tarihi ve işlem tarihi PDF'de görünür.

### **4. Database Kaydı**
- Tüm mutabakat verileri SQL Server database'de saklanır.
- Hash doğrulaması için veriler database'den çekilir ve yeniden hesaplanır.
- Database kayıtları değiştirilemez (audit trail).

---

## ⚖️ Yasal Geçerlilik

### **5070 Sayılı Elektronik İmza Kanunu**

**Madde 5:**
> "Güvenli elektronik imza, elle atılan imza ile aynı hukuki sonucu doğurur."

**Madde 4:**
> "Elektronik imza, elektronik veriye eklenen veya elektronik veriyle mantıksal bağlantısı bulunan ve kimlik doğrulama amacıyla kullanılan elektronik veridir."

### **6102 Sayılı TTK (Türk Ticaret Kanunu)**

**Madde 18/3:**
> "Ticari defterler ve belgeler, Türkiye'de bulunan ve kanuni yollara başvurma hakkı saklı kalmak kaydıyla, aksine delil getirilinceye kadar, sicile kayıtlı tacirler arasındaki ticari ilişkilerden doğan davalarında delil teşkil eder."

### **6098 Sayılı TBK (Türk Borçlar Kanunu)**

**Madde 88:**
> "Alacaklı ile borçlu, borç ilişkisinin kapsamı ve içeriği hakkında mutabakata vardıklarında, bu mutabakat sözleşmesi hükmündedir."

---

## 🛡️ Sahtecilik Tespiti

### **Belge Sahte İse Ne Olur?**

1. **Hash Eşleşmez:**
   - API `"gecerli": false` döner.
   - Mesaj: "Dijital imza GEÇERSİZ!"

2. **Mutabakat Numarası Bulunamaz:**
   - API 404 hatası verir.
   - Belge hiç oluşturulmamıştır.

3. **Veriler Tutarsız:**
   - PDF'deki tutarlar ile database tutarları farklıysa tespit edilir.

---

## 📞 Teknik Destek

### **Mahkeme/Bilirkişi Desteği**

**Dino Gıda San. Tic. Ltd. Şti.**
- **Adres:** Görece Cumhuriyet Mah. Gülçırpı Cad. No:19 Menderes İzmir
- **Telefon:** 0850 220 45 66
- **E-posta:** info@dinogida.com.tr
- **Web:** www.dinogida.com.tr

### **Sistem Yöneticisi**
- **Ad:** Hüseyin ve İbrahim Kaplan
- **E-posta:** info@dinogida.com.tr

### **Teknik Dokümanlar**
- API Endpoint: `https://api.dinogida.com.tr/docs`
- Swagger UI: Tüm endpoint'leri test edebilirsiniz

---

## 📊 Örnek Kullanım Senaryoları

### **Senaryo 1: Mahkeme Tarafından Doğrulama**

Bir ticari uyuşmazlıkta davacı taraf, PDF mutabakat belgesini delil olarak sunar.

**Adımlar:**
1. Mahkeme bilirkişisi, PDF'deki mutabakat numarasını ve dijital imzayı not eder.
2. API'ye POST request gönderir.
3. API, database'den verileri çeker ve hash'i yeniden hesaplar.
4. Eğer hash eşleşirse → **Belge orijinaldir** (Delil olarak kabul edilir).
5. Eğer hash eşleşmezse → **Belge değiştirilmiştir** (Delil olarak reddedilir).

---

### **Senaryo 2: Şirket İç Denetimi**

Muhasebe departmanı, geçmiş bir mutabakatın doğruluğunu kontrol etmek istiyor.

**Adımlar:**
1. Arşivdeki PDF'i açarlar.
2. Mutabakat numarasını ve dijital imzayı okurlar.
3. API'ye sorgu gönderirler.
4. Sistem, belgenin geçerliliğini onaylar.

---

### **Senaryo 3: Müşteri Tarafından Red İddiası**

Müşteri, "Bu belgeyi ben onaylamadım" diyor.

**Kontrol:**
1. PDF'deki IP adresi kontrol edilir → Hangi ISP kullanıldı?
2. Tarih/saat bilgisi kontrol edilir → Onay hangi tarihte yapıldı?
3. Database'deki activity log kontrol edilir → Hangi kullanıcı işlemi yaptı?
4. Hash doğrulaması yapılır → Belge değiştirilmiş mi?

---

## 🧪 Test Örnekleri

### **Test Case 1: Geçerli Belge**

```bash
curl -X POST "https://api.dinogida.com.tr/api/verify/mutabakat" \
  -H "Content-Type: application/json" \
  -d '{
    "mutabakat_no": "MUT-20251020230253-I4MU",
    "dijital_imza": "0432dca0be20ae0e124c9dc3a2aef39f8516d1267af184476a4d96b4b40abc8"
  }'
```

**Beklenen Sonuç:** `"gecerli": true`

---

### **Test Case 2: Değiştirilmiş Belge**

PDF'deki bir tutar manuel olarak değiştirilirse:

```bash
# Hash aynı ama belgede değişiklik var
curl -X POST "https://api.dinogida.com.tr/api/verify/mutabakat" \
  -H "Content-Type: application/json" \
  -d '{
    "mutabakat_no": "MUT-20251020230253-I4MU",
    "dijital_imza": "YANLIS_HASH_DEGERI"
  }'
```

**Beklenen Sonuç:** `"gecerli": false`

---

## 📜 Sonuç

Bu sistem, **matematiksel kesinlik** ile belgenin orijinalliğini kanıtlar. Mahkemeler ve yasal otoriteler, bu API'yi kullanarak elektronik mutabakat belgelerinin geçerliliğini güvenle doğrulayabilir.

**Avantajlar:**
- ✅ Anlık doğrulama
- ✅ Değiştirilemez kayıt
- ✅ Yasal geçerlilik
- ✅ Kolay kullanım
- ✅ Ücretsiz erişim

---

**Son Güncelleme:** 20 Ekim 2025  
**Versiyon:** 1.0.0  
**Hazırlayan:** Dino Gıda IT Departmanı

