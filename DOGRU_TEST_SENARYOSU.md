# ✅ Doğru Test Senaryosu - Müşteri Onaylama

## 🚫 YANLIŞ KULLANIM

```
❌ musteri1 ile giriş yap
❌ Yeni Mutabakat oluştur
❌ Kendine mutabakat gönder
❌ Onayla/Reddet butonları YOK!
```

**Neden YOK?**
- Müşteri = GÖNDEREN (sender)
- Müşteri kendi gönderdiği mutabakatı onaylayamaz!
- Onayla/Reddet sadece ALICI (receiver) için!

---

## ✅ DOĞRU KULLANIM

### 1️⃣ ADIM 1: Admin/Muhasebe ile Giriş Yap

```
Kullanıcı: admin
Şifre: Dino2025!
```

veya

```
Kullanıcı: muhasebe
Şifre: Muhasebe2025!
```

### 2️⃣ ADIM 2: Yeni Mutabakat Oluştur

1. Sol menüden **"Yeni Mutabakat"** tıkla
2. **Alıcı seç:** `musteri1` (Örnek Müşteri 1)
3. **Dönem:**
   - Başlangıç: 01.01.2025
   - Bitiş: 31.01.2025
4. **Kalem ekle:**
   ```
   Tarih: 14.01.2025
   Belge No: FT-2025-001
   Açıklama: Ürün Alışı
   Borç: 50,000.00
   Alacak: 0.00
   ```
5. **"Kaydet"** tıkla

### 3️⃣ ADIM 3: Mutabakatı Gönder

1. Mutabakat listesinde "Taslak" olarak görünür
2. **"Görüntüle"** tıkla
3. **"Gönder"** butonuna tıkla (Yeşil, uçak simgeli)
4. Durum "Gönderildi" olur

### 4️⃣ ADIM 4: Çıkış Yap

Sağ üstten **"Çıkış"** tıkla

### 5️⃣ ADIM 5: Müşteri ile Giriş Yap

```
Kullanıcı: musteri1
Şifre: Musteri123!
```

### 6️⃣ ADIM 6: Mutabakatı Gör

- **Dashboard'da:** "1 adet mutabakat onayınızı bekliyor!" mesajı görünür
- **Mutabakatlar sayfasında:** 
  - 🟡 Sarı satır (yanıp söner)
  - "Gönderildi ⏳" badge'i
  - **"İncele & Onayla"** butonu

### 7️⃣ ADIM 7: Detaya Gir

**"İncele & Onayla"** butonuna tıkla

### 8️⃣ ADIM 8: Butonları Gör! ✅

Şimdi göreceksiniz:
- 🟢 **"Onayla"** butonu (Yeşil, onay simgeli)
- 🔴 **"Reddet"** butonu (Kırmızı, çarpı simgeli)

### 9️⃣ ADIM 9: Console Kontrolü

F12 > Console:
```javascript
User: { id: 4, role: "musteri", username: "musteri1" }
Mutabakat: { 
  sender_id: 1,    ← Dino Gıda (admin)
  receiver_id: 4,  ← musteri1 (SİZ!)
  durum: "gonderildi" 
}
Yetkiler: {
  isSender: false,    ← Gönderen DEĞİLsiniz
  isReceiver: true,   ← Alıcısınız! ✓
  canApprove: true,   ← Onaylayabilirsiniz! ✓
  canReject: true     ← Reddedebilirsiniz! ✓
}
```

### 🔟 ADIM 10: Onayla veya Reddet

**Onaylamak için:**
1. **"Onayla"** tıkla
2. Başarı mesajı görüntülenir
3. Durum "Onaylandı" olur

**Reddetmek için:**
1. **"Reddet"** tıkla
2. Popup açılır
3. Red nedeni yaz: "15.01.2025 tarihli fatura kayıtlarda yok"
4. **"Reddet"** tıkla

---

## 🔍 Neden Butonlar Görünmüyor?

### Senaryo 1: Kendi Mutabakatınızı Oluşturdunuz
```
musteri1 → Mutabakat oluşturdu
         → sender_id = 4 (musteri1)
         → receiver_id = ? (başka biri)
         → isReceiver = false
         → canApprove = false ❌
```

### Senaryo 2: Size Gönderilmemiş
```
admin → Mutabakat oluşturdu
      → receiver_id = 5 (başka müşteri)
      → Siz musteri1 (id: 4)
      → isReceiver = false ❌
      → canApprove = false ❌
```

### Senaryo 3: Durum Taslak
```
admin → Mutabakat oluşturdu
      → receiver_id = 4 (musteri1) ✓
      → Ama henüz GÖNDERMED İ
      → durum = "taslak"
      → canApprove = false ❌
```

### Senaryo 4: DOĞRU! ✅
```
admin → Mutabakat oluşturdu
      → receiver_id = 4 (musteri1) ✓
      → GÖNDERDİ
      → durum = "gonderildi" ✓
      → isReceiver = true ✓
      → canApprove = true ✅
      → BUTONLAR GÖRÜNÜR! 🎉
```

---

## 📊 Roller ve Yetkiler

| Rol | Oluştur | Gönder | Onayla | Reddet | Sil |
|-----|---------|--------|--------|--------|-----|
| **Admin** | ✅ | ✅ | ❌ | ❌ | ✅ |
| **Muhasebe** | ✅ | ✅ | ❌ | ❌ | ✅ |
| **Planlama** | ✅ | ✅ | ❌ | ❌ | ✅ |
| **Müşteri** | ❌ | ❌ | ✅ | ✅ | ❌ |

---

## 🎯 Özet

1. **Müşteri mutabakat OLUŞTURAMAZ**
2. **Admin/Muhasebe/Planlama oluşturur**
3. **Müşteriye GÖNDER İR**
4. **Müşteri GÖRÜR ve ONAYLAR/REDDEDER**

---

**Şimdi doğru senaryoyu deneyin! Admin ile oluştur, gönder, sonra musteri1 ile onayla! 🚀**

