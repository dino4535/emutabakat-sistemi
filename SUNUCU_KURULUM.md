# 🚀 SUNUCU KURULUM ADIMLARI

## Adım 1: Sunucuya Bağlan ve Git Clone Yap

```bash
# SSH ile sunucuya bağlan
ssh root@85.209.120.101

# /opt dizinine git
cd /opt

# GitHub'dan clone et
git clone https://github.com/dino4535/emutabakat-sistemi.git emutabakat

# Dizine gir
cd emutabakat

# Dosyaların geldiğini kontrol et
ls -la
```

## Adım 2: .env Dosyası Oluştur

```bash
# Template'ten kopyala
cp env.production.example .env

# SECRET_KEY üret
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Çıktıyı kopyala, sonra .env'yi düzenle
nano .env
```

### .env İçeriği:

```bash
DATABASE_URL=mssql+pyodbc://mutabakat_user:PASSWORD@85.209.120.57:1433/Mutabakat?driver=ODBC+Driver+17+for+SQL+Server
SECRET_KEY=<yukarıda-ürettiğiniz-key>
REDIS_PASSWORD=emutabakat2025
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@emutabakat.com
FLOWER_USER=admin
FLOWER_PASSWORD=admin2025
```

**CTRL+X → Y → Enter** ile kaydet

```bash
# İzinleri kısıtla
chmod 600 .env
```

## Adım 3: Gerekli Dizinleri Oluştur

```bash
mkdir -p fonts certificates uploads pdfs
```

## Adım 4: Portainer'da Deploy Et

### Yöntem 1: Web Editor (Önerilen)

1. **https://85.209.120.101:9443** adresine git
2. **Stacks** → **+ Add stack**
3. **Name:** `emutabakat`
4. **Build method:** Web editor
5. Aşağıdaki içeriği yapıştır:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: emutabakat-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-emutabakat2025}
    volumes:
      - redis_data:/data
    networks:
      - emutabakat-network

  backend:
    build:
      context: /opt/emutabakat
      dockerfile: backend/Dockerfile
    container_name: emutabakat-backend
    restart: unless-stopped
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=30
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD:-emutabakat2025}
      - REDIS_DB=0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD:-emutabakat2025}@redis:6379/1
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD:-emutabakat2025}@redis:6379/2
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_PORT=${SMTP_PORT:-587}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - SMTP_FROM_EMAIL=${SMTP_FROM_EMAIL}
      - SMTP_FROM_NAME=E-Mutabakat Sistemi
    volumes:
      - /opt/emutabakat/fonts:/app/fonts
      - /opt/emutabakat/certificates:/app/certificates
      - /opt/emutabakat/uploads:/app/uploads
      - /opt/emutabakat/pdfs:/app/pdfs
      - backend_logs:/app/logs
    depends_on:
      - redis
    networks:
      - emutabakat-network

  celery-worker:
    build:
      context: /opt/emutabakat
      dockerfile: backend/Dockerfile
    container_name: emutabakat-celery-worker
    restart: unless-stopped
    command: celery -A backend.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD:-emutabakat2025}
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD:-emutabakat2025}@redis:6379/1
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD:-emutabakat2025}@redis:6379/2
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_PORT=${SMTP_PORT:-587}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - SMTP_FROM_EMAIL=${SMTP_FROM_EMAIL}
    volumes:
      - /opt/emutabakat/fonts:/app/fonts
      - /opt/emutabakat/certificates:/app/certificates
      - /opt/emutabakat/uploads:/app/uploads
      - /opt/emutabakat/pdfs:/app/pdfs
      - worker_logs:/app/logs
    depends_on:
      - redis
      - backend
    networks:
      - emutabakat-network

  celery-beat:
    build:
      context: /opt/emutabakat
      dockerfile: backend/Dockerfile
    container_name: emutabakat-celery-beat
    restart: unless-stopped
    command: celery -A backend.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD:-emutabakat2025}
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD:-emutabakat2025}@redis:6379/1
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD:-emutabakat2025}@redis:6379/2
    volumes:
      - beat_logs:/app/logs
    depends_on:
      - redis
      - backend
    networks:
      - emutabakat-network

  flower:
    build:
      context: /opt/emutabakat
      dockerfile: backend/Dockerfile
    container_name: emutabakat-flower
    restart: unless-stopped
    command: celery -A backend.celery_app flower --port=5555
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD:-emutabakat2025}@redis:6379/1
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD:-emutabakat2025}@redis:6379/2
      - FLOWER_BASIC_AUTH=${FLOWER_USER:-admin}:${FLOWER_PASSWORD:-admin2025}
    ports:
      - "5555:5555"
    depends_on:
      - redis
      - celery-worker
    networks:
      - emutabakat-network

  frontend:
    build:
      context: /opt/emutabakat/frontend
      dockerfile: Dockerfile
    container_name: emutabakat-frontend
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - emutabakat-network

networks:
  emutabakat-network:
    driver: bridge

volumes:
  redis_data:
  backend_logs:
  worker_logs:
  beat_logs:
```

6. **Environment variables** bölümünde **Advanced mode** aç
7. `.env` dosyanızın içeriğini yapıştır
8. **Deploy the stack**

### Yöntem 2: Terminal'den (Daha Hızlı)

```bash
cd /opt/emutabakat
docker-compose up -d --build
```

## Adım 5: Kontrol Et

```bash
# Konteyner durumlarını kontrol et
docker ps

# Logları kontrol et
docker logs emutabakat-backend
docker logs emutabakat-frontend

# Frontend erişimi
curl http://localhost
```

## Başarılı! 🎉

Frontend: http://85.209.120.101
Backend API: http://85.209.120.101/api/docs
Flower: http://85.209.120.101:5555

