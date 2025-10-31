# Project Brief

Bu proje, çok şirketli (multi-company) bir E-Mutabakat sistemi sunar. Temel hedefler:

- Mutabakat (borç/alacak) oluşturma, gönderme, onaylama/ret akışları
- VKN/TC bazlı manuel mutabakat ve bayi detay yönetimi
- Dijital imza (pyHanko) ile PDF üretimi ve doğrulama (public doğrulama sayfası)
- KVKK uyum süreçleri: onay toplama, loglama ve silme kayıtları
- Güçlü güvenlik: başarısız giriş takibi, brute-force koruması, hesap kilitleme
- Modern web arayüzü (React) ve mobil uyumluluk
- Docker ile dağıtım (frontend Nginx, backend FastAPI)

Başarı ölçütleri:
- Üretimde kesintisiz çalışır, mobilde kararlı navigasyon
- Doğru şirket logoları ve çok-şirket bağlamında veri izolasyonu
- KVKK ve yasal delil kayıtlarının tam olması

