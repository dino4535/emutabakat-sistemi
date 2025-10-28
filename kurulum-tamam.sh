#!/bin/bash

###############################################################################
# E-MUTABAKAT SİSTEMİ - TAM OTOMATİK KURULUM SCRIPTİ
# Ubuntu 22.04 LTS - ROOT ile çalıştırın
# Kullanıcı oluşturma + Sistem kurulumu + Docker yapılandırması
###############################################################################

set -e

# Renkli çıktı
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Kullanıcı bilgileri
NEW_USER="oguz"
NEW_USER_PASSWORD="Oguz2024!Mutabakat"  # Değiştirin!

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║     E-MUTABAKAT SİSTEMİ - TAM OTOMATİK KURULUM               ║"
echo "║     Root ile çalıştırılmalıdır!                              ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Root kontrolü
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}[HATA] Bu scripti root olarak çalıştırın!${NC}"
    echo "Kullanım: sudo bash kurulum-tamam.sh"
    exit 1
fi

sleep 2

###############################################################################
# 1. KULLANICI OLUŞTUR
###############################################################################

echo -e "\n${GREEN}[1/12]${NC} Kullanıcı '$NEW_USER' oluşturuluyor..."

# Kullanıcı zaten var mı?
if id "$NEW_USER" &>/dev/null; then
    echo -e "${YELLOW}[UYARI]${NC} Kullanıcı '$NEW_USER' zaten mevcut, atlanıyor..."
else
    # Kullanıcı oluştur (şifre ile)
    useradd -m -s /bin/bash "$NEW_USER"
    echo "$NEW_USER:$NEW_USER_PASSWORD" | chpasswd
    
    # Sudo yetkisi ver
    usermod -aG sudo "$NEW_USER"
    
    echo -e "${GREEN}✓${NC} Kullanıcı oluşturuldu!"
    echo -e "${BLUE}  Kullanıcı: $NEW_USER${NC}"
    echo -e "${BLUE}  Şifre: $NEW_USER_PASSWORD${NC}"
fi

###############################################################################
# 2. SİSTEM GÜNCELLEMELERİ
###############################################################################

echo -e "\n${GREEN}[2/12]${NC} Sistem güncellemeleri yapılıyor..."

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq

echo -e "${GREEN}✓${NC} Sistem güncellemeleri tamamlandı!"

###############################################################################
# 3. GEREKLI PAKETLER
###############################################################################

echo -e "\n${GREEN}[3/12]${NC} Gerekli paketler kuruluyor..."

apt-get install -y -qq \
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    net-tools \
    unzip \
    zip \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw \
    fail2ban \
    unattended-upgrades

echo -e "${GREEN}✓${NC} Gerekli paketler kuruldu!"

###############################################################################
# 4. DOCKER KURULUMU
###############################################################################

echo -e "\n${GREEN}[4/12]${NC} Docker kuruluyor..."

if command -v docker &> /dev/null; then
    echo -e "${YELLOW}[UYARI]${NC} Docker zaten kurulu! Versiyon: $(docker --version)"
else
    # Docker GPG anahtarı
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Docker kurulumu
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Docker'ı başlat
    systemctl enable docker
    systemctl start docker
    
    echo -e "${GREEN}✓${NC} Docker kuruldu! Versiyon: $(docker --version)"
fi

# Kullanıcıyı docker grubuna ekle
usermod -aG docker "$NEW_USER"
echo -e "${GREEN}✓${NC} '$NEW_USER' kullanıcısı docker grubuna eklendi"

###############################################################################
# 5. FIREWALL AYARLARI (UFW)
###############################################################################

echo -e "\n${GREEN}[5/12]${NC} Firewall ayarları yapılıyor..."

# UFW'yi etkinleştir
ufw --force enable

# SSH portunu aç (kritik!)
ufw allow 22/tcp comment 'SSH' > /dev/null 2>&1
echo -e "${GREEN}✓${NC} SSH portu (22) açıldı"

# HTTP ve HTTPS
ufw allow 80/tcp comment 'HTTP' > /dev/null 2>&1
ufw allow 443/tcp comment 'HTTPS' > /dev/null 2>&1
echo -e "${GREEN}✓${NC} HTTP (80) ve HTTPS (443) portları açıldı"

# Backend API (development)
ufw allow 8000/tcp comment 'Backend API' > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Backend API portu (8000) açıldı"

echo -e "${GREEN}✓${NC} Firewall ayarları tamamlandı!"

###############################################################################
# 6. MICROSOFT SQL SERVER ODBC DRIVER
###############################################################################

echo -e "\n${GREEN}[6/12]${NC} Microsoft SQL Server ODBC Driver kuruluyor..."

# Microsoft GPG anahtarı
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc > /dev/null

# Microsoft repository
curl -fsSL https://packages.microsoft.com/config/ubuntu/22.04/prod.list | tee /etc/apt/sources.list.d/mssql-release.list > /dev/null

# Paketleri güncelle
apt-get update -qq

# ODBC Driver kur
ACCEPT_EULA=Y apt-get install -y -qq msodbcsql18 unixodbc-dev

echo -e "${GREEN}✓${NC} ODBC Driver kuruldu!"

###############################################################################
# 7. SWAP DOSYASI OLUŞTUR (4GB)
###############################################################################

echo -e "\n${GREEN}[7/12]${NC} Swap dosyası oluşturuluyor..."

if [ -f /swapfile ]; then
    echo -e "${YELLOW}[UYARI]${NC} Swap dosyası zaten mevcut!"
else
    # 4GB Swap oluştur
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile > /dev/null
    swapon /swapfile
    
    # Kalıcı yap
    if ! grep -q '/swapfile' /etc/fstab; then
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
    fi
    
    echo -e "${GREEN}✓${NC} 4GB Swap dosyası oluşturuldu!"
fi

###############################################################################
# 8. PROJE KLASÖR YAPISINI OLUŞTUR
###############################################################################

echo -e "\n${GREEN}[8/12]${NC} Proje klasörleri oluşturuluyor..."

# Ana klasör
mkdir -p /opt/mutabakat
chown -R $NEW_USER:$NEW_USER /opt/mutabakat

# Alt klasörler (oguz kullanıcısı olarak)
su - $NEW_USER <<'EOF'
cd /opt/mutabakat
mkdir -p nginx/conf.d
mkdir -p nginx/ssl
mkdir -p certificates
mkdir -p pdfs
mkdir -p logs
mkdir -p musteri1/backend
mkdir -p musteri1/frontend
EOF

echo -e "${GREEN}✓${NC} Klasör yapısı oluşturuldu: /opt/mutabakat/"

###############################################################################
# 9. DOCKER DOSYALARINI OLUŞTUR
###############################################################################

echo -e "\n${GREEN}[9/12]${NC} Docker yapılandırma dosyaları oluşturuluyor..."

# docker-compose.yml
cat > /opt/mutabakat/musteri1/docker-compose.yml <<'COMPOSE_EOF'
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: mutabakat_backend
    environment:
      - DB_HOST=${DB_HOST:-85.209.120.57}
      - DB_NAME=${DB_NAME:-Mutabakat}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - SECRET_KEY=${SECRET_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ../pdfs:/app/pdfs
      - ../certificates:/app/certificates
      - ../logs:/app/logs
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
COMPOSE_EOF

# .env template
cat > /opt/mutabakat/musteri1/.env.example <<'ENV_EOF'
# Database Configuration
DB_HOST=85.209.120.57
DB_NAME=Mutabakat
DB_USER=sa
DB_PASSWORD=YOUR_SQL_SERVER_PASSWORD_HERE
SECRET_KEY=YOUR_SECRET_KEY_MIN_32_CHARS_HERE

# Application
APP_NAME=E-Mutabakat
APP_ENV=production
ENV_EOF

# Backend Dockerfile (DÜZELTİLMİŞ!)
cat > /opt/mutabakat/musteri1/backend/Dockerfile <<'BACKEND_EOF'
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

# Microsoft ODBC Driver (modern yöntem)
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

# DÜZELTİLMİŞ CMD - backend klasöründen main.py'yi çalıştır
CMD ["uvicorn", "main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
BACKEND_EOF

# Frontend Dockerfile (DÜZELTİLMİŞ!)
cat > /opt/mutabakat/musteri1/frontend/Dockerfile <<'FRONTEND_EOF'
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
# DÜZELTİLMİŞ - devDependencies de kurulacak (vite için gerekli)
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
FRONTEND_EOF

# Frontend Nginx config
cat > /opt/mutabakat/musteri1/frontend/nginx.conf <<'NGINX_EOF'
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
        
        # Timeout ayarları
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Cache static files
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_EOF

# Dosya sahipliklerini ayarla
chown -R $NEW_USER:$NEW_USER /opt/mutabakat

echo -e "${GREEN}✓${NC} Docker yapılandırma dosyaları oluşturuldu!"

###############################################################################
# 10. GÜVENLİK AYARLARI
###############################################################################

echo -e "\n${GREEN}[10/12]${NC} Güvenlik ayarları yapılıyor..."

# Fail2Ban (SSH brute force koruması)
systemctl enable fail2ban > /dev/null 2>&1
systemctl start fail2ban > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Fail2Ban aktif edildi"

# Unattended upgrades (otomatik güvenlik güncellemeleri)
echo 'APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";' > /etc/apt/apt.conf.d/20auto-upgrades
echo -e "${GREEN}✓${NC} Otomatik güvenlik güncellemeleri aktif edildi"

###############################################################################
# 11. SİSTEM OPTİMİZASYONLARI
###############################################################################

echo -e "\n${GREEN}[11/12]${NC} Sistem optimizasyonları yapılıyor..."

# Timezone ayarla (Türkiye)
timedatectl set-timezone Europe/Istanbul > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Zaman dilimi: Europe/Istanbul"

# Locale ayarla
locale-gen tr_TR.UTF-8 > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Locale: tr_TR.UTF-8"

# Hostname ayarla
hostnamectl set-hostname mutabakat-prod > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Hostname: mutabakat-prod"

###############################################################################
# 12. DEPLOY SCRIPTİ OLUŞTUR
###############################################################################

echo -e "\n${GREEN}[12/12]${NC} Deploy scripti oluşturuluyor..."

cat > /opt/mutabakat/musteri1/deploy.sh <<'DEPLOY_EOF'
#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     E-MUTABAKAT SİSTEMİ - DEPLOYMENT                         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

cd /opt/mutabakat/musteri1

echo -e "${YELLOW}[1/5]${NC} Ön kontroller..."

if [ ! -f ".env" ]; then
    echo -e "${RED}[HATA]${NC} .env dosyası bulunamadı!"
    echo "Lütfen .env dosyasını oluşturun:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

if [ ! -f "backend/requirements.txt" ]; then
    echo -e "${RED}[HATA]${NC} Backend dosyaları yüklenmemiş!"
    exit 1
fi

if [ ! -f "frontend/package.json" ]; then
    echo -e "${RED}[HATA]${NC} Frontend dosyaları yüklenmemiş!"
    exit 1
fi

echo -e "${GREEN}✓${NC} Ön kontroller başarılı!"

echo -e "\n${YELLOW}[2/5]${NC} Eski container'lar durduruluyor..."
docker compose down > /dev/null 2>&1 || true

echo -e "\n${YELLOW}[3/5]${NC} Docker image'ları build ediliyor..."
echo -e "${BLUE}Bu işlem 5-10 dakika sürebilir...${NC}"
docker compose build

echo -e "\n${YELLOW}[4/5]${NC} Container'lar başlatılıyor..."
docker compose up -d

echo -e "\n${YELLOW}[5/5]${NC} Sağlık kontrolü..."
sleep 10

BACKEND_HEALTH=$(curl -s http://localhost:8000/health || echo "FAIL")
if echo "$BACKEND_HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC} Backend çalışıyor!"
else
    echo -e "${RED}✗${NC} Backend hatası! Logları kontrol edin:"
    echo "  docker logs mutabakat_backend"
fi

FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✓${NC} Frontend çalışıyor!"
else
    echo -e "${RED}✗${NC} Frontend hatası!"
fi

echo -e "\n${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           ✓ DEPLOYMENT TAMAMLANDI!                           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

IP_ADDR=$(hostname -I | awk '{print $1}')

echo -e "${BLUE}ERİŞİM BİLGİLERİ:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Frontend:     http://$IP_ADDR"
echo "🔧 Backend API:  http://$IP_ADDR:8000"
echo "📊 API Docs:     http://$IP_ADDR:8000/docs"
echo "💚 Health:       http://$IP_ADDR:8000/health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
DEPLOY_EOF

chmod +x /opt/mutabakat/musteri1/deploy.sh
chown $NEW_USER:$NEW_USER /opt/mutabakat/musteri1/deploy.sh

echo -e "${GREEN}✓${NC} Deploy scripti oluşturuldu!"

###############################################################################
# KURULUM TAMAMLANDI
###############################################################################

echo -e "\n${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║           ✓ KURULUM BAŞARIYLA TAMAMLANDI!                    ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "\n${BLUE}KULLANİCİ BİLGİLERİ:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Kullanıcı Adı: ${GREEN}$NEW_USER${NC}"
echo "Şifre:         ${GREEN}$NEW_USER_PASSWORD${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "\n${BLUE}SONRAKI ADIMLAR:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Root'tan çık:"
echo "   ${YELLOW}exit${NC}"
echo ""
echo "2. $NEW_USER kullanıcısı ile bağlan:"
echo "   ${YELLOW}ssh $NEW_USER@$(hostname -I | awk '{print $1}')${NC}"
echo ""
echo "3. Proje dosyalarını yükle (FileZilla/WinSCP):"
echo "   ${YELLOW}Hedef: /opt/mutabakat/musteri1/${NC}"
echo "   - backend/ klasörü (backend/backend/ dahil!)"
echo "   - frontend/ klasörü"
echo "   - certificates/dino_gida.p12"
echo ""
echo "4. .env dosyasını yapılandır:"
echo "   ${YELLOW}cd /opt/mutabakat/musteri1${NC}"
echo "   ${YELLOW}cp .env.example .env${NC}"
echo "   ${YELLOW}nano .env${NC}"
echo "   (DB_PASSWORD ve SECRET_KEY'i gir)"
echo ""
echo "5. Deploy et:"
echo "   ${YELLOW}cd /opt/mutabakat/musteri1${NC}"
echo "   ${YELLOW}./deploy.sh${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "\n${GREEN}İyi çalışmalar! 🚀${NC}\n"

