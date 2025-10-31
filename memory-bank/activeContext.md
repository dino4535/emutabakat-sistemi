# Active Context

Güncel Odak
- Mobil uyumluluk: sidebar, header, responsive tablolar; iOS 100vh/safe-area düzeltmeleri
- Kullanıcı yönetimi: 422 hatası; payload eşlemesi ve boş alan filtreleme

Son Değişiklikler
- Header mobilde gizlendi; hızlı işlemler sidebar’a taşındı
- Sidebar z-index ve backdrop sırası düzeltildi; nav tıklamalarından sonra menü kapanıyor
- CreateByVKN/Detail/VerifySignature tabloları responsive hâle getirildi
- PublicApproval/Auth sayfalarında `--vh` ve safe-area padding eklendi
- UserManagement: `tax_number -> vkn_tckn` map; update payload’da boş alanlar siliniyor

Gündemdeki Sonraki Adımlar
- Sunucuda tam temizlik sonrası dağıtım rutinleştirme (deploy.sh)
- Mobil sayfa bazlı son kontroller (Dashboard, List, Detay, Public)
- Kullanıcı güncellemede edge-case’ler (rol/aktiflik kombinasyonları) test

Önemli Tercihler
- UI: tablo -> kart dönüşümü 768px altında
- Güvenlik: ActivityLogger, FailedLoginTracker; IP/ISP kaydı
