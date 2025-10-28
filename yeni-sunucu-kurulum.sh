#!/bin/bash

#############################################
# E-MUTABAKAT - TAM OTOMATİK KURULUM
# Ubuntu 22.04 LTS için
#############################################

set -e

# Renkler
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Kullanıcı bilgileri
USER_NAME="oguz"
USER_PASSWORD="Oguz2024!Mutabakat"
DB_HOST="85.209.120.57"
DB_NAME="Mutabakat"
SECRET_KEY="dino-mutabakat-2024-prod-k8Hx9mP2vN5qR7wL3jT6yU4bF8eG1aZ0"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_error() {
    echo -e "${RED}[HATA]${NC} $1"
}

log_step() {
    echo -e "\n${YELLOW}==>${NC} $1"
}

#############################################
# 1. ESKİ KURULUM TEMİZLİĞİ
#############################################
cleanup_old_installation() {
    log_step "Eski kurulum temizleniyor..."
    
    # Container'ları durdur ve sil
    if [ -d "/opt/mutabakat/musteri1" ]; then
        cd /opt/mutabakat/musteri1
        if [ -f "docker-compose.yml" ]; then
            docker compose down 2>/dev/null || true
        fi
    fi
    
    # Eski dosyaları sil (certificates ve pdfs hariç)
    if [ -d "/opt/mutabakat/musteri1" ]; then
        rm -rf /opt/mutabakat/musteri1/*
    fi
    
    log_success "Eski kurulum temizlendi"
}

#############################################
# 2. KULLANICI OLUŞTUR/GÜNCELLE
#############################################
setup_user() {
    log_step "Kullanıcı ayarları yapılıyor..."
    
    if id "$USER_NAME" &>/dev/null; then
        log_info "Kullanıcı $USER_NAME zaten mevcut"
    else
        log_info "Kullanıcı $USER_NAME oluşturuluyor..."
        useradd -m -s /bin/bash -G sudo,docker "$USER_NAME"
        echo "$USER_NAME:$USER_PASSWORD" | chpasswd
        log_success "Kullanıcı oluşturuldu"
    fi
    
    # Docker grubuna ekle
    usermod -aG docker "$USER_NAME" 2>/dev/null || true
    
    log_success "Kullanıcı ayarları tamamlandı"
}

#############################################
# 3. PROJE KLASÖRÜ YAPISINI OLUŞTUR
#############################################
create_project_structure() {
    log_step "Proje klasör yapısı oluşturuluyor..."
    
    mkdir -p /opt/mutabakat/musteri1/{backend,frontend}
    mkdir -p /opt/mutabakat/{certificates,pdfs,logs}
    
    log_success "Klasör yapısı oluşturuldu"
}

#############################################
# 4. DOCKER-COMPOSE.YML OLUŞTUR
#############################################
create_docker_compose() {
    log_step "docker-compose.yml oluşturuluyor..."
    
    cat > /opt/mutabakat/musteri1/docker-compose.yml << 'EOFCOMPOSE'
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: mutabakat_backend
    environment:
      - DB_HOST=85.209.120.57
      - DB_NAME=Mutabakat
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - SECRET_KEY=${SECRET_KEY}
    ports:
      - "8000:8000"
    volumes:
      - /opt/mutabakat/pdfs:/app/pdfs
      - /opt/mutabakat/certificates:/app/certificates
      - /opt/mutabakat/logs:/app/logs
    restart: unless-stopped
    networks:
      - mutabakat_network

  frontend:
    build: ./frontend
    container_name: mutabakat_frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - mutabakat_network

networks:
  mutabakat_network:
    driver: bridge
EOFCOMPOSE

    log_success "docker-compose.yml oluşturuldu"
}

#############################################
# 5. .env.example OLUŞTUR
#############################################
create_env_example() {
    log_step ".env.example oluşturuluyor..."
    
    cat > /opt/mutabakat/musteri1/.env.example << EOFENV
# Database Configuration
DB_HOST=${DB_HOST}
DB_NAME=${DB_NAME}
DB_USER=sa
DB_PASSWORD=YOUR_SQL_SERVER_PASSWORD_HERE
SECRET_KEY=${SECRET_KEY}

# Application
APP_NAME=E-Mutabakat
APP_ENV=production
EOFENV

    log_success ".env.example oluşturuldu"
}

#############################################
# 6. BACKEND DOCKERFILE OLUŞTUR
#############################################
create_backend_dockerfile() {
    log_step "Backend Dockerfile oluşturuluyor..."
    
    cat > /opt/mutabakat/musteri1/backend/Dockerfile << 'EOFDOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

# Sistem paketleri
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    unixodbc \
    unixodbc-dev \
    gnupg2 \
    && rm -rf /var/lib/apt/lists/*

# Microsoft ODBC Driver
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-archive-keyring.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyala
COPY . .

# Klasörleri oluştur
RUN mkdir -p pdfs certificates logs fonts

EXPOSE 8000

CMD ["uvicorn", "main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
EOFDOCKERFILE

    log_success "Backend Dockerfile oluşturuldu"
}

#############################################
# 7. FRONTEND DOCKERFILE OLUŞTUR
#############################################
create_frontend_dockerfile() {
    log_step "Frontend Dockerfile oluşturuluyor..."
    
    cat > /opt/mutabakat/musteri1/frontend/Dockerfile << 'EOFDOCKERFILE'
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOFDOCKERFILE

    log_success "Frontend Dockerfile oluşturuldu"
}

#############################################
# 8. FRONTEND NGINX CONFIG OLUŞTUR
#############################################
create_nginx_config() {
    log_step "Nginx config oluşturuluyor..."
    
    cat > /opt/mutabakat/musteri1/frontend/nginx.conf << 'EOFNGINX'
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 180s;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
EOFNGINX

    log_success "Nginx config oluşturuldu"
}

#############################################
# 9. DEPLOY SCRIPT OLUŞTUR
#############################################
create_deploy_script() {
    log_step "deploy.sh oluşturuluyor..."
    
    cat > /opt/mutabakat/musteri1/deploy.sh << 'EOFDEPLOY'
#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_error() { echo -e "${RED}[HATA]${NC} $1"; }
log_step() { echo -e "\n${YELLOW}==>${NC} $1"; }

echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════╗
║   E-MUTABAKAT SİSTEMİ - DEPLOYMENT        ║
╚═══════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Kontroller
check_prerequisites() {
    log_step "Ön kontroller yapılıyor..."
    
    if [ ! -f ".env" ]; then
        log_error ".env dosyası bulunamadı!"
        log_info "Lütfen .env dosyasını oluşturun: cp .env.example .env"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker kurulu değil!"
        exit 1
    fi
    
    log_success "Ön kontroller başarılı"
}

# Eski container'ları durdur
stop_existing_containers() {
    log_step "Mevcut container'lar durduruluyor..."
    sudo docker compose down 2>/dev/null || true
    log_success "Container'lar durduruldu"
}

# Image'ları build et
build_docker_images() {
    log_step "Docker image'ları build ediliyor..."
    log_info "Bu işlem 5-10 dakika sürebilir..."
    
    if ! sudo docker compose build; then
        log_error "Build hatası!"
        exit 1
    fi
    
    log_success "Build tamamlandı"
}

# Container'ları başlat
start_containers() {
    log_step "Container'lar başlatılıyor..."
    
    if ! sudo docker compose up -d; then
        log_error "Container başlatma hatası!"
        exit 1
    fi
    
    log_success "Container'lar başlatıldı"
}

# Sağlık kontrolü
health_check() {
    log_step "Sağlık kontrolü yapılıyor..."
    
    sleep 10
    
    # Backend
    for i in {1..30}; do
        if curl -s http://localhost:8000/health | grep -q "healthy"; then
            log_success "Backend çalışıyor!"
            break
        fi
        sleep 2
    done
    
    # Frontend
    if curl -s http://localhost/ | grep -q "<!DOCTYPE html>"; then
        log_success "Frontend çalışıyor!"
    fi
}

# Ana işlem
check_prerequisites
stop_existing_containers
build_docker_images
start_containers
health_check

echo -e "\n${GREEN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         DEPLOYMENT BAŞARILI! 🚀           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}\n"

echo -e "${BLUE}Frontend:${NC} http://$(hostname -I | awk '{print $1}')"
echo -e "${BLUE}Backend API:${NC} http://$(hostname -I | awk '{print $1}'):8000"
echo -e "${BLUE}API Docs:${NC} http://$(hostname -I | awk '{print $1}'):8000/docs\n"
EOFDEPLOY

    chmod +x /opt/mutabakat/musteri1/deploy.sh
    log_success "deploy.sh oluşturuldu"
}

#############################################
# 10. İZİNLERİ DÜZELT
#############################################
fix_permissions() {
    log_step "Dosya izinleri düzenleniyor..."
    
    chown -R ${USER_NAME}:${USER_NAME} /opt/mutabakat
    chmod -R 755 /opt/mutabakat
    
    log_success "İzinler düzenlendi"
}

#############################################
# ANA İŞLEM
#############################################
main() {
    echo -e "${GREEN}"
    cat << "EOF"
╔═══════════════════════════════════════════╗
║   E-MUTABAKAT - OTOMATİK KURULUM          ║
║   Ubuntu 22.04 LTS                        ║
╚═══════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    # Root kontrolü
    if [ "$EUID" -ne 0 ]; then
        log_error "Bu script root olarak çalıştırılmalı!"
        exit 1
    fi
    
    cleanup_old_installation
    setup_user
    create_project_structure
    create_docker_compose
    create_env_example
    create_backend_dockerfile
    create_frontend_dockerfile
    create_nginx_config
    create_deploy_script
    fix_permissions
    
    echo -e "\n${GREEN}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║      SUNUCU HAZIR! 🎉                     ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}\n"
    
    echo -e "${YELLOW}SONRAKİ ADIMLAR:${NC}"
    echo -e "1. ${BLUE}oguz${NC} kullanıcısı ile bağlanın:"
    echo -e "   ${GREEN}ssh oguz@85.209.120.101${NC}"
    echo -e "   Şifre: ${YELLOW}${USER_PASSWORD}${NC}\n"
    
    echo -e "2. Proje dosyalarını yükleyin (SFTP/FileZilla):"
    echo -e "   ${BLUE}/opt/mutabakat/musteri1/backend/${NC} ← backend dosyaları"
    echo -e "   ${BLUE}/opt/mutabakat/musteri1/frontend/${NC} ← frontend dosyaları"
    echo -e "   ${BLUE}/opt/mutabakat/certificates/${NC} ← dino_gida.p12\n"
    
    echo -e "3. .env dosyasını yapılandırın:"
    echo -e "   ${GREEN}cd /opt/mutabakat/musteri1${NC}"
    echo -e "   ${GREEN}cp .env.example .env${NC}"
    echo -e "   ${GREEN}nano .env${NC} (DB_PASSWORD girin)\n"
    
    echo -e "4. Deploy edin:"
    echo -e "   ${GREEN}./deploy.sh${NC}\n"
}

main

