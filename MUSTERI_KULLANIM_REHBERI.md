# 📋 Müşteri Kullanım Rehberi - E-Mutabakat Sistemi

## 🎯 Müşteri Neler Yapabilir?

### ✅ YAPABİLİR
- Kendisine gönderilen mutabakatları görüntüleme
- Mutabakatları onaylama
- Mutabakatları reddetme (red nedeni ile)
- Dashboard'da istatistiklerini görme
- Mutabakat detaylarını ve kalemlerini inceleme

### ❌ YAPAMAZ
- Yeni mutabakat oluşturma
- Mutabakat silme
- Başkalarının mutabakatlarını görme
- Toplu mutabakat işlemleri

---

## 🚀 Müşteri Girişi

### 1️⃣ Sisteme Giriş
```
URL: http://localhost:3000
Kullanıcı: musteri1
Şifre: Musteri123!
```

### 2️⃣ Dashboard
Giriş yaptıktan sonra göreceğiniz bilgiler:
- **Toplam Mutabakat**: Size gönderilen tüm mutabakatlar
- **Bekleyen**: Onayınızı bekleyen mutabakatlar
- **Onaylanan**: Onayladığınız mutabakatlar
- **Reddedilen**: Reddettiğiniz mutabakatlar
- **Mali Özet**: Toplam borç/alacak durumu

---

## 📄 Mutabakat Onaylama Süreci

### Adım 1: Mutabakatlar Sayfasına Git
Sol menüden **"Mutabakatlar"** tıklayın.

### Adım 2: Bekleyen Mutabakatı Seç
**"Gönderildi"** durumundaki mutabakatları göreceksiniz:
- 🟡 **Sarı Badge**: Gönderildi (Onayınızı bekliyor)
- 🟢 **Yeşil Badge**: Onaylandı
- 🔴 **Kırmızı Badge**: Reddedildi
- ⚪ **Gri Badge**: Taslak

### Adım 3: Mutabakat Detayını Aç
**"Görüntüle"** butonuna tıklayın.

### Adım 4: Bilgileri İncele
Şunları kontrol edin:
- ✅ **Gönderen**: Dino Gıda San. Tic. Ltd. Şti.
- ✅ **Dönem**: Başlangıç ve bitiş tarihleri
- ✅ **Kalemler**: Tüm işlemler ve tutarlar
  - Tarih
  - Belge No
  - Açıklama
  - Borç tutarı
  - Alacak tutarı
- ✅ **Özet**: Toplam borç, alacak ve bakiye

### Adım 5A: ONAYLAMA
Mutabakat doğruysa:
1. **"Onayla"** butonuna tıklayın (Yeşil buton)
2. Onay mesajı görüntülenir
3. Durum **"Onaylandı"** olarak güncellenir
4. E-posta bildirimi gönderilir (yakında)

### Adım 5B: REDDETME
Mutabakatta hata varsa:
1. **"Reddet"** butonuna tıklayın (Kırmızı buton)
2. Red nedeni popup'ı açılır
3. **Red nedenini detaylı yazın**:
   ```
   Örnek: "15.01.2025 tarihli FT-2024-100 nolu fatura 
   kayıtlarımızda bulunmuyor. Kontrol edilmesini rica ederim."
   ```
4. **"Reddet"** butonuna tıklayın
5. Durum **"Reddedildi"** olarak güncellenir
6. Dino Gıda'ya bildirim gider

---

## 🎨 Ekran Görünümü

### Müşteri Dashboard
```
┌─────────────────────────────────────────┐
│ Dashboard                                │
├─────────────────────────────────────────┤
│ 📊 İstatistikler                        │
│                                          │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│ │  10  │ │  3   │ │  5   │ │  2   │   │
│ │Toplam│ │Bekl. │ │Onay. │ │Red.  │   │
│ └──────┘ └──────┘ └──────┘ └──────┘   │
│                                          │
│ 💰 Mali Özet                            │
│ Toplam Borç:   125,450.00 ₺            │
│ Toplam Alacak:  98,320.00 ₺            │
│ Bakiye:        -27,130.00 ₺            │
└─────────────────────────────────────────┘
```

### Mutabakat Detay Ekranı
```
┌─────────────────────────────────────────┐
│ ← Geri    MUT-20250120143022-AB45       │
│                          🟡 Gönderildi   │
├─────────────────────────────────────────┤
│ Gönderen: Dino Gıda                     │
│ Dönem: 01 Ocak 2025 - 31 Ocak 2025     │
│                                          │
│ 📋 Kalemler                             │
│ ┌─────────────────────────────────────┐ │
│ │ 15.01 | FT-001 | Alış  | 10,000₺  │ │
│ │ 20.01 | FT-002 | Alış  | 15,000₺  │ │
│ │ 25.01 | İRSL   | İade  | -2,000₺  │ │
│ └─────────────────────────────────────┘ │
│                                          │
│ 💰 Özet                                 │
│ Toplam Borç:   25,000₺                  │
│ Toplam Alacak:  2,000₺                  │
│ Bakiye:        23,000₺                  │
│                                          │
│ [✓ Onayla]  [✗ Reddet]                 │
└─────────────────────────────────────────┘
```

---

## ⚠️ Önemli Notlar

### Onay Verirken Dikkat Edin
✅ Tüm kalemleri kontrol edin
✅ Tutar ve tarihleri doğrulayın
✅ Belge numaralarını karşılaştırın
✅ Bakiyenin doğru olduğundan emin olun

### Reddetme Nedenleri
Açık ve net yazın:
- ❌ "Hatalı" (yetersiz)
- ✅ "15.01.2025 tarihli FT-100 nolu fatura kayıtlarda yok"

- ❌ "Tutmaz" (yetersiz)
- ✅ "20.01.2025 ödeme kayıtlarda 5.000₺, belgede 6.000₺ görünüyor"

### Durum Değişiklikleri
- **Gönderildi** → **Onaylandı**: Geri alınamaz!
- **Gönderildi** → **Reddedildi**: Dino Gıda düzeltip tekrar gönderebilir
- **Onaylandı**: Artık değiştirilemez
- **Reddedildi**: Düzeltme yapılıp tekrar gönderilebilir

---

## 📱 Mobil Kullanım

Sistemimiz responsive tasarımdır:
- 📱 Telefon
- 📲 Tablet
- 💻 Bilgisayar

Her cihazda sorunsuz çalışır!

---

## 🆘 Sorun Giderme

### "Onaylama butonu göremiyorum"
✅ Kontrol: Mutabakat size gönderilmiş mi?
✅ Kontrol: Durum "Gönderildi" mi?
✅ Kontrol: Müşteri hesabı ile mi giriş yaptınız?

### "Mutabakatımı bulamıyorum"
✅ "Mutabakatlar" sayfasına gidin
✅ Durum filtresini kontrol edin
✅ Admin/Muhasebe ile iletişime geçin

### "Yanlışlıkla onayladım"
❌ Onayı geri alamazsınız
✅ Hemen Dino Gıda ile iletişime geçin
✅ Muhasebe departmanına bildirin

---

## 📞 İletişim

Sorun yaşarsanız:
- **Muhasebe**: muhasebe@dinogida.com
- **Planlama**: planlama@dinogida.com
- **Admin**: admin@dinogida.com

---

## 🎓 Kısa Özet

1. **Giriş Yap** → http://localhost:3000
2. **Mutabakatlar** → Bekleyen mutabakatları gör
3. **Detaya Tıkla** → Kalemleri incele
4. **Onayla** veya **Reddet** (neden ile)
5. **Tamamlandı!** ✓

---

**Kolay Kullanım, Hızlı Onay! 🚀**

