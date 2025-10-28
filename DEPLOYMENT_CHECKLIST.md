# ✅ DEPLOYMENT KONTROL LİSTESİ

## 📋 DEPLOY ÖNCESİ HAZIRLIK

### **1. Dosya Hazırlığı**
- [ ] Tüm kod değişiklikleri tamamlandı
- [ ] Backend testleri geçti
- [ ] Frontend build başarılı
- [ ] Fontlar (`fonts/` dizini) hazır
- [ ] Dijital sertifikalar (`certificates/` dizini) hazır
- [ ] Logo dosyaları mevcut

### **2. Environment Variables**
- [ ] `env.production.example` dosyasından `.env` oluşturuldu
- [ ] `DATABASE_URL` doğru SQL Server bilgileriyle güncellendi
- [ ] `SECRET_KEY` rastgele 64 karakterlik key ile değiştirildi
- [ ] `REDIS_PASSWORD` güçlü bir şifre olarak ayarlandı
- [ ] `SMTP_*` değerleri yapılandırıldı (email için)
- [ ] `FLOWER_PASSWORD` değiştirildi
- [ ] `.env` dosyası `chmod 600` ile korundu

### **3. Sunucu Gereksinimleri**
- [ ] Docker kurulu
- [ ] Docker Compose kurulu
- [ ] Portainer çalışıyor (85.209.120.101:9443)
- [ ] SQL Server erişilebilir (85.209.120.57:1433)
- [ ] Minimum 4GB RAM
- [ ] Minimum 20GB disk alanı
- [ ] Port 80 açık (HTTP)
- [ ] Port 443 açık (HTTPS - gelecek için)

---

## 🚀 DEPLOYMENT ADIMLARI

### **ADIM 1: Dosya Transferi**
- [ ] Tüm proje dosyaları `/opt/emutabakat/` dizinine yüklendi
- [ ] Dosya izinleri doğru (`chmod -R 755 /opt/emutabakat`)
- [ ] `.env` dosyası oluşturuldu ve yapılandırıldı
- [ ] `fonts/` klasörü kopyalandı
- [ ] `certificates/` klasörü kopyalandı

### **ADIM 2: Docker Build**
- [ ] Portainer'da "Stacks" → "Add stack" açıldı
- [ ] Stack adı: `emutabakat` girildi
- [ ] `docker-compose.yml` içeriği yapıştırıldı
- [ ] Environment variables eklendi
- [ ] "Deploy the stack" butonuna tıklandı
- [ ] Image download tamamlandı (5-10 dakika)

### **ADIM 3: Konteyner Kontrolü**
Tüm konteynerların durumu:
- [ ] `emutabakat-redis` - healthy
- [ ] `emutabakat-backend` - healthy
- [ ] `emutabakat-celery-worker` - running
- [ ] `emutabakat-celery-beat` - running
- [ ] `emutabakat-flower` - running
- [ ] `emutabakat-frontend` - healthy

### **ADIM 4: Log Kontrolü**
Her konteyner için loglar kontrol edildi:
- [ ] Backend: "Uvicorn running" mesajı görünüyor
- [ ] Backend: "Redis cache baglantisi basarili" mesajı var
- [ ] Backend: "Veritabani baglantisi basarili" mesajı var
- [ ] Frontend: Nginx başladı
- [ ] Redis: "Ready to accept connections" mesajı var
- [ ] Celery Worker: "celery@... ready" mesajı var

---

## 🧪 TEST ADIMLARI

### **1. Health Check**
```bash
# Backend health
curl http://85.209.120.101/api/health
# Expected: {"status": "healthy"}

# Frontend
curl http://85.209.120.101/
# Expected: HTML response
```

### **2. Frontend Erişimi**
- [ ] http://85.209.120.101 açılıyor
- [ ] Login sayfası yükleniyor
- [ ] Stil dosyaları düzgün yükleniyor
- [ ] Logo görünüyor
- [ ] Responsive tasarım çalışıyor (mobile test)

### **3. Backend API Testi**
- [ ] http://85.209.120.101/api/docs açılıyor (Swagger UI)
- [ ] "/health" endpoint çalışıyor
- [ ] "/api/auth/login" endpoint çalışıyor

### **4. Login Testi**
- [ ] Kullanıcı adı ve şifre ile giriş yapılıyor
- [ ] JWT token alınıyor
- [ ] Dashboard'a yönlendiriliyor
- [ ] KVKK popup açılıyor (ilk girişte)

### **5. Dashboard Testi**
- [ ] İstatistikler yükleniyor
- [ ] Grafik ve kartlar görünüyor
- [ ] Cache çalışıyor (Redis loglarından kontrol)
- [ ] Sayfa yükleme süresi < 1 saniye

### **6. Mutabakat İşlemleri**
- [ ] Mutabakat listesi açılıyor
- [ ] Yeni mutabakat oluşturuluyor
- [ ] PDF oluşturuluyor ve indiriliyor
- [ ] PDF dijital imzalı
- [ ] Mutabakat gönderiliyor
- [ ] Email bildirimi gidiyor (SMTP yapılandırıldıysa)

### **7. Excel Yükleme**
- [ ] Kullanıcı Excel yükleme çalışıyor
- [ ] Mutabakat Excel yükleme çalışıyor
- [ ] Hata durumunda rollback yapılıyor
- [ ] Başarı mesajları görünüyor

### **8. Celery ve Async Tasks**
- [ ] Flower arayüzü açılıyor (http://85.209.120.101:5555)
- [ ] Worker'lar "online" durumda
- [ ] PDF generation task çalışıyor
- [ ] Email task çalışıyor
- [ ] Scheduled tasks görünüyor (Beat)

### **9. WebSocket Testi**
- [ ] WebSocket bağlantısı kuruluyor
- [ ] Real-time bildirimler geliyor
- [ ] Mutabakat durum değişikliği anında güncelleniyor
- [ ] Bağlantı koptuğunda otomatik yeniden bağlanıyor

### **10. Performance Testi**
- [ ] Dashboard yükleme < 500ms (Redis ile)
- [ ] API response time < 200ms
- [ ] PDF generation async çalışıyor (timeout yok)
- [ ] Bulk işlemler async çalışıyor
- [ ] Memory kullanımı stabil

---

## 🔒 GÜVENLİK KONTROLLERİ

### **Sunucu Güvenliği**
- [ ] Firewall aktif
- [ ] Sadece gerekli portlar açık (80, 443, 9443)
- [ ] SSH key authentication kullanılıyor
- [ ] Root login devre dışı
- [ ] Fail2ban kurulu (opsiyonel)

### **Uygulama Güvenliği**
- [ ] `.env` dosyası korunmuş (chmod 600)
- [ ] SQL injection koruması var (SQLAlchemy ORM)
- [ ] XSS koruması var (React)
- [ ] CSRF token kullanılıyor
- [ ] Rate limiting aktif
- [ ] JWT token expire süresi ayarlı (30 dakika)
- [ ] Password hashleme (bcrypt) çalışıyor

### **Database Güvenliği**
- [ ] SQL Server şifresi güçlü
- [ ] Database sadece backend'den erişilebilir
- [ ] Backup mekanizması mevcut
- [ ] SQL Server firewall kuralları ayarlı

### **Docker Güvenliği**
- [ ] Konteynerlar non-root user ile çalışıyor
- [ ] Image'lar güncel
- [ ] Hassas bilgiler environment variable'larda
- [ ] Volume izinleri doğru

---

## 📊 MONITORING KURULUMU

### **1. Portainer Monitoring**
- [ ] Portainer'da Container Stats açık
- [ ] Resource kullanımı izleniyor
- [ ] Alert kuralları ayarlandı (opsiyonel)

### **2. Flower (Celery Monitoring)**
- [ ] http://85.209.120.101:5555 erişilebilir
- [ ] Basic auth şifresi değiştirildi
- [ ] Worker durumları görünüyor
- [ ] Task success/failure oranları izleniyor

### **3. Log Management**
- [ ] Docker logs düzenli kontrol ediliyor
- [ ] Log rotation ayarlandı
- [ ] Kritik hata bildirimleri ayarlandı (opsiyonel)

### **4. Backup**
- [ ] SQL Server otomatik backup yapılandırıldı
- [ ] Redis persistence aktif (AOF)
- [ ] Docker volumes için backup script hazırlandı
- [ ] Backup test edildi (restore)

---

## 🌐 PRODUCTION OPTIMIZASYONLARI

### **1. SSL/TLS Sertifikası (Öncelikli!)**
- [ ] Let's Encrypt sertifikası alındı
- [ ] Nginx SSL yapılandırıldı
- [ ] HTTP → HTTPS yönlendirmesi aktif
- [ ] HSTS header eklendi

### **2. Domain Yapılandırması**
- [ ] Domain DNS'i yapılandırıldı
- [ ] A record: emutabakat.com → 85.209.120.101
- [ ] www subdomain yapılandırıldı
- [ ] SSL sertifikası domain için geçerli

### **3. CDN ve Caching (Opsiyonel)**
- [ ] Cloudflare veya benzeri CDN ayarlandı
- [ ] Static asset'ler CDN'den servis ediliyor
- [ ] Browser caching headers ayarlandı

### **4. Performance Tuning**
- [ ] Docker resource limits ayarlandı
- [ ] Redis maxmemory yapılandırıldı
- [ ] Nginx worker_processes optimize edildi
- [ ] Database connection pool ayarlandı

### **5. Monitoring (İleri Seviye)**
- [ ] Prometheus + Grafana kuruldu (opsiyonel)
- [ ] Sentry error tracking entegre edildi (opsiyonel)
- [ ] Uptime monitoring (UptimeRobot, etc.)

---

## 🎉 DEPLOYMENT TAMAMLANDI!

### **Erişim Adresleri:**
```
✅ Frontend:         http://85.209.120.101
✅ Backend API:      http://85.209.120.101/api
✅ API Docs:         http://85.209.120.101/api/docs
✅ Health Check:     http://85.209.120.101/api/health
✅ Flower (Celery):  http://85.209.120.101:5555
✅ Portainer:        https://85.209.120.101:9443
```

### **Default Login:**
- Username: bermer_admin (veya kendi oluşturduğunuz admin)
- Password: VKN'in son 6 hanesi

---

## 📞 DESTEK VE DOKÜMANTASYON

- **Hızlı Başlangıç:** PORTAINER_QUICK_START.md
- **Detaylı Rehber:** PORTAINER_DEPLOY_GUIDE.md
- **Bugünkü İşler:** BUGUN_YAPILAN_ISLER.md
- **Geliştirme Planı:** GELISTIRME_PLANI_V2.md

---

## 🔄 SONRAKI ADIMLAR

1. **Acil (1 gün içinde):**
   - [ ] SSL sertifikası ekle
   - [ ] Domain bağla
   - [ ] Firewall kurallarını sıkılaştır
   - [ ] Backup test et

2. **Önemli (1 hafta içinde):**
   - [ ] Monitoring altyapısı kur
   - [ ] Performance tuning yap
   - [ ] Security audit yap
   - [ ] Kullanıcı eğitimi ver

3. **Gelecek (1 ay içinde):**
   - [ ] Faz 2 (Güvenlik) özelliklerini ekle
   - [ ] 2FA implementasyonu
   - [ ] Advanced monitoring
   - [ ] CDN entegrasyonu

---

**Başarılı bir deployment! 🚀**

_Sorularınız için dokümanlara bakın veya destek alın._

