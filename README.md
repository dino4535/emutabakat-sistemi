# 🏢 E-Mutabakat Sistemi

Modern, güvenli ve kullanıcı dostu cari hesap mutabakatı yönetim sistemi.

## 📋 İçindekiler

- [Özellikler](#-özellikler)
- [Teknoloji Stack](#-teknoloji-stack)
- [Kurulum](#-kurulum)
- [Deployment](#-deployment)
- [Dokümantasyon](#-dokümantasyon)
- [Lisans](#-lisans)

---

## ✨ Özellikler

### 🔐 Güvenlik
- JWT token authentication
- Bcrypt password hashing
- Rate limiting (SlowAPI)
- Failed login tracking
- IP ve ISP takibi
- KVKK compliance
- Dijital imza (pyhanko)
- 256-bit AES PDF encryption

### 👥 Multi-Tenant (Çok Şirketli)
- Her şirketin kendi verisi
- VKN bazlı kullanıcı sistemi
- Şirket bazlı branding (logo, renk)
- Şirket bazlı KVKK metinleri
- Company-level izolasyon

### 💼 İş Özellikleri
- Mutabakat oluşturma ve yönetimi
- PDF oluşturma (Türkçe karakter desteği)
- Dijital imza ve watermark
- Email bildirimleri
- SMS entegrasyonu (NetGSM)
- Excel toplu yükleme
- VKN bazlı bayi yönetimi
- Yasal raporlar

### 🎨 Modern UI/UX
- Responsive design (mobile-first)
- Loading states & animations
- Advanced table filtering
- PDF preview modal
- Skeleton loaders
- Form validation
- WCAG 2.1 AA accessibility

### ⚡ Performans & Optimizasyon
- Redis caching (%85-90 hızlanma)
- Celery async tasks (PDF, email, SMS)
- WebSocket real-time updates
- Performance monitoring
- Background job processing
- Database indexing

---

## 🛠️ Teknoloji Stack

### Backend
- **Framework:** FastAPI 0.109.0
- **ORM:** SQLAlchemy 2.0.25
- **Database:** Microsoft SQL Server
- **Cache & Queue:** Redis
- **Task Queue:** Celery
- **PDF:** reportlab, pyhanko, pikepdf
- **Authentication:** JWT (python-jose)
- **Security:** bcrypt, slowapi

### Frontend
- **Framework:** React 18
- **Router:** React Router v6
- **HTTP Client:** Axios
- **State Management:** React Query
- **UI Components:** Custom components
- **Styling:** CSS Modules
- **Build Tool:** Vite

### DevOps
- **Containerization:** Docker & Docker Compose
- **Orchestration:** Portainer
- **Monitoring:** Flower (Celery), Performance middleware
- **Reverse Proxy:** Nginx

---

## 🚀 Kurulum

### Gereksinimler
- Python 3.11+
- Node.js 18+
- SQL Server
- Redis (opsiyonel, yüksek performans için önerilen)
- Docker & Docker Compose (production için)

### Yerel Development

#### Backend
```bash
# Virtual environment oluştur
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Bağımlılıkları yükle
pip install -r requirements.txt

# .env dosyası oluştur
cp .env.example .env
# .env dosyasını düzenle

# Başlat
python start_backend.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

#### Celery Worker & Beat (Opsiyonel)
```bash
# Worker
python start_celery_worker.py

# Beat (Scheduled tasks)
python start_celery_beat.py
```

#### Redis (Opsiyonel)
```bash
# Docker ile
docker run -d -p 6379:6379 redis:7-alpine

# Windows - Chocolatey ile
choco install redis-64 -y
redis-server
```

---

## 🌐 Deployment

### Seçenek 1: Git + Portainer (Önerilen) ⭐

**Hızlı başlangıç:**
```bash
# 1. Yerel repo'yu GitHub/GitLab'a push et
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/emutabakat-sistemi.git
git push -u origin main

# 2. Sunucuda clone et
ssh root@YOUR_SERVER_IP
cd /opt
git clone https://github.com/YOUR_USERNAME/emutabakat-sistemi.git emutabakat
cd emutabakat

# 3. Environment yapılandır
cp env.production.example .env
nano .env  # Değerleri düzenle
chmod 600 .env

# 4. Portainer'da deploy et
# https://YOUR_SERVER_IP:9443
# Stacks → Add stack → emutabakat
# docker-compose.yml yükle ve deploy et
```

**Detaylı rehber:** [GIT_DEPLOYMENT_GUIDE.md](GIT_DEPLOYMENT_GUIDE.md)

### Seçenek 2: Manuel Deployment

**Detaylı rehber:** [PORTAINER_DEPLOY_GUIDE.md](PORTAINER_DEPLOY_GUIDE.md)

**Hızlı başlangıç:** [PORTAINER_QUICK_START.md](PORTAINER_QUICK_START.md)

---

## 📚 Dokümantasyon

### Deployment
- [Git ile Deployment](GIT_DEPLOYMENT_GUIDE.md) - Git tabanlı deployment ⭐
- [Portainer Deployment Rehberi](PORTAINER_DEPLOY_GUIDE.md) - Detaylı manuel kurulum
- [Portainer Hızlı Başlangıç](PORTAINER_QUICK_START.md) - 3 adımda deploy
- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md) - Kontrol listesi

### Geliştirme
- [Bugün Yapılan İşler](BUGUN_YAPILAN_ISLER.md) - Son değişiklikler
- [Geliştirme Planı v2](GELISTIRME_PLANI_V2.md) - Roadmap
- [Redis Caching](REDIS_CACHING_COMPLETED.md) - Cache implementasyonu
- [Celery Background Jobs](CELERY_BACKGROUND_JOBS_COMPLETED.md) - Async task sistemi
- [WebSocket & Performance](WEBSOCKET_PERFORMANCE_COMPLETED.md) - Real-time ve monitoring

---

## 🏗️ Proje Yapısı

```
Proje1/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── database.py             # Database connection
│   ├── models/                 # SQLAlchemy models
│   ├── routers/                # API endpoints
│   ├── utils/                  # Helper functions
│   ├── tasks/                  # Celery tasks
│   ├── websocket/              # WebSocket handlers
│   ├── middleware/             # Custom middleware
│   ├── templates/              # Email templates
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── hooks/              # Custom hooks
│   │   ├── utils/              # Utilities
│   │   └── styles/             # CSS files
│   ├── Dockerfile
│   └── nginx.conf              # Nginx config
│
├── fonts/                      # Turkish fonts
├── certificates/               # Digital certificates
├── docker-compose.yml          # Docker orchestration
├── requirements.txt            # Python dependencies
└── README.md
```

---

## 🔧 Yapılandırma

### Environment Variables

`.env` dosyası oluşturun:

```bash
# Database
DATABASE_URL=mssql+pyodbc://user:password@host:1433/database?driver=ODBC+Driver+17+for+SQL+Server

# Security
SECRET_KEY=your-secret-key-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (Opsiyonel)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Email (Opsiyonel)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@emutabakat.com
```

---

## 🧪 Testing

```bash
# Backend tests
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

---

## 📊 Monitoring

### Production Monitoring
- **Portainer:** Container stats ve logs
- **Flower:** Celery task monitoring (http://your-server:5555)
- **Performance Middleware:** API response time tracking
- **Health Check:** http://your-server/api/health

### Development
```bash
# Backend logs
python start_backend.py

# Celery worker logs
python start_celery_worker.py

# Frontend logs
cd frontend && npm run dev
```

---

## 🔄 Güncelleme

### Git ile (Önerilen)
```bash
# Yerel değişiklikler
git add .
git commit -m "Update: Description"
git push origin main

# Sunucuda
ssh root@YOUR_SERVER
cd /opt/emutabakat
git pull origin main
docker-compose up -d --build
```

### Portainer ile
1. Stacks → emutabakat → Editor
2. "Pull and redeploy" butonuna tıkla

---

## 🆘 Sorun Giderme

### Backend başlamıyor
```bash
# Logs kontrol et
docker logs emutabakat-backend

# Database bağlantısını test et
# .env dosyasında DATABASE_URL'i kontrol et
```

### Redis bağlantı hatası
```bash
# Redis çalışıyor mu?
docker ps | grep redis

# Redis'e bağlan
docker exec -it emutabakat-redis redis-cli
auth your-password
ping  # Response: PONG
```

### Frontend 502 hatası
```bash
# Backend hazır mı bekle (1-2 dakika)
curl http://localhost:8000/health
```

**Daha fazla:** [PORTAINER_DEPLOY_GUIDE.md - Sorun Giderme](PORTAINER_DEPLOY_GUIDE.md#-sorun-giderme)

---

## 🎯 Performans

| Metrik | Önce | Sonra | İyileşme |
|--------|------|-------|----------|
| Dashboard Load | 500-800ms | 50-100ms | **%85-90** |
| PDF Generation | 5-10s blocking | Async | **Non-blocking** |
| Bulk SMS | 200s timeout | Async | **Non-blocking** |
| Excel Processing | 30s timeout | Async | **Non-blocking** |
| Real-time Updates | Polling | WebSocket | **%95** |

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add: AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📝 Changelog

### v1.0.0 (27 Ekim 2025)
- ✅ Initial release
- ✅ Multi-tenant architecture
- ✅ Redis caching
- ✅ Celery background jobs
- ✅ WebSocket real-time
- ✅ Modern responsive UI
- ✅ Docker deployment ready

**Detaylı:** [BUGUN_YAPILAN_ISLER.md](BUGUN_YAPILAN_ISLER.md)

---

## 🛣️ Roadmap

### Faz 2: Güvenlik Sağlamlaştırma
- [ ] Two-Factor Authentication (2FA)
- [ ] Security Headers
- [ ] Session Management
- [ ] CSRF Protection
- [ ] Security Audit Logs

**Detaylı:** [GELISTIRME_PLANI_V2.md](GELISTIRME_PLANI_V2.md)

---

## 📄 Lisans

Bu proje özel lisans altındadır. Ticari kullanım için izin gereklidir.

---

## 👥 İletişim

**Proje Sahibi:** E-Mutabakat Ekibi

**Destek:** support@emutabakat.com

**Dokümantasyon:** [Wiki](https://github.com/YOUR_USERNAME/emutabakat-sistemi/wiki)

---

## 🙏 Teşekkürler

Bu proje aşağıdaki açık kaynak projelerden yararlanmaktadır:
- FastAPI
- React
- SQLAlchemy
- Celery
- Redis
- Docker

---

**⭐ Projeyi beğendiyseniz yıldız vermeyi unutmayın!**

**Made with ❤️ in Turkey 🇹🇷**
