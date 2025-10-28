# Frontend User Test

## Kontrol Listesi

1. **Browser Console açın** (F12)
2. **Mutabakat detayına gidin**
3. **Console'da şunları kontrol edin:**

```javascript
// Şunları görmeli:
User: {
  id: X,
  username: "...",
  role: "musteri" veya "MUSTERI",
  ...
}

Mutabakat: {
  sender_id: Y,
  receiver_id: X,
  durum: "gonderildi"
}

Yetkiler: {
  isSender: false,
  isReceiver: true,
  isCustomer: true,
  canApprove: true,
  canReject: true
}
```

## Beklenen Sonuç

Eğer:
- `isReceiver: true`
- `durum: "gonderildi"`

İse "Onayla" ve "Reddet" butonları görünmeli!

## Sorun Varsa

1. Backend'den user bilgisi doğru geliyor mu?
2. role field'ı "musteri" mi yoksa "MUSTERI" mi?
3. receiver_id ile current_user.id eşleşiyor mu?

