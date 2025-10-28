#!/bin/bash

###############################################################################
# E-MUTABAKAT SİSTEMİ - DEPLOYMENT SCRIPTİ
# Proje dosyalarını deploy etmek ve Docker container'ları başlatmak için
###############################################################################

set -e

# Renkli çıktı
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/opt/mutabakat/musteri1"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║        E-MUTABAKAT SİSTEMİ - DEPLOYMENT                      ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

###############################################################################
# KONTROLLER
###############################################################################

echo -e "${YELLOW}[1/6]${NC} Ön kontroller yapılıyor..."

# Docker kontrolü
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[HATA]${NC} Docker kurulu değil! Önce setup-server.sh çalıştırın."
    exit 1
fi

# Klasör kontrolü
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}[HATA]${NC} Proje klasörü bulunamadı: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

# .env kontrolü
if [ ! -f ".env" ]; then
    echo -e "${RED}[HATA]${NC} .env dosyası bulunamadı!"
    echo -e "${YELLOW}Lütfen .env dosyasını oluşturun:${NC}"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Backend dosyaları kontrolü
if [ ! -f "backend/requirements.txt" ]; then
    echo -e "${RED}[HATA]${NC} Backend dosyaları yüklenmemiş!"
    echo "Lütfen backend klasörünü /opt/mutabakat/musteri1/backend/ içine yükleyin"
    exit 1
fi

# Frontend dosyaları kontrolü
if [ ! -f "frontend/package.json" ]; then
    echo -e "${RED}[HATA]${NC} Frontend dosyaları yüklenmemiş!"
    echo "Lütfen frontend klasörünü /opt/mutabakat/musteri1/frontend/ içine yükleyin"
    exit 1
fi

echo -e "${GREEN}✓${NC} Ön kontroller başarılı!"

###############################################################################
# ESKİ CONTAINER'LARI DURDUR
###############################################################################

echo -e "\n${YELLOW}[2/6]${NC} Eski container'lar kontrol ediliyor..."

if docker ps -a | grep -q mutabakat; then
    echo "Eski container'lar durduruluyor..."
    docker compose down
    echo -e "${GREEN}✓${NC} Eski container'lar durduruldu"
else
    echo "Aktif container bulunamadı"
fi

###############################################################################
# DOCKER IMAGE'LARI BUILD ET
###############################################################################

echo -e "\n${YELLOW}[3/6]${NC} Docker image'ları build ediliyor..."
echo -e "${BLUE}Bu işlem 5-10 dakika sürebilir. Lütfen bekleyin...${NC}"

# --no-cache kullanmak isterseniz:
# docker compose build --no-cache
docker compose build

echo -e "${GREEN}✓${NC} Docker image'ları hazır!"

###############################################################################
# CONTAINER'LARI BAŞLAT
###############################################################################

echo -e "\n${YELLOW}[4/6]${NC} Container'lar başlatılıyor..."

docker compose up -d

echo -e "${GREEN}✓${NC} Container'lar başlatıldı!"

###############################################################################
# SAĞLIK KONTROLÜ
###############################################################################

echo -e "\n${YELLOW}[5/6]${NC} Sağlık kontrolü yapılıyor..."

# 10 saniye bekle (container'lar başlasın)
echo "Container'ların başlaması bekleniyor..."
sleep 10

# Backend kontrolü
echo -n "Backend API kontrol ediliyor... "
BACKEND_HEALTH=$(curl -s http://localhost:8000/health || echo "FAIL")
if echo "$BACKEND_HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Çalışıyor${NC}"
else
    echo -e "${RED}✗ Hata!${NC}"
    echo "Backend logları:"
    docker compose logs backend | tail -20
fi

# Frontend kontrolü
echo -n "Frontend kontrol ediliyor... "
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Çalışıyor${NC}"
else
    echo -e "${RED}✗ Hata! (HTTP: $FRONTEND_STATUS)${NC}"
    echo "Frontend logları:"
    docker compose logs frontend | tail -20
fi

###############################################################################
# ÖZET BİLGİLER
###############################################################################

echo -e "\n${YELLOW}[6/6]${NC} Container durumu:"
docker ps --filter "name=mutabakat" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo -e "\n${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║           ✓ DEPLOYMENT TAMAMLANDI!                           ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# IP adresi al
IP_ADDR=$(hostname -I | awk '{print $1}')

echo -e "${BLUE}ERİŞİM BİLGİLERİ:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Frontend:        http://$IP_ADDR"
echo "🔧 Backend API:     http://$IP_ADDR:8000"
echo "📊 API Docs:        http://$IP_ADDR:8000/docs"
echo "💚 Health Check:    http://$IP_ADDR:8000/health"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "\n${BLUE}YARARLI KOMUTLAR:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Logları izle:"
echo "  ${YELLOW}docker compose logs -f${NC}"
echo ""
echo "Sadece backend logları:"
echo "  ${YELLOW}docker compose logs -f backend${NC}"
echo ""
echo "Container durumu:"
echo "  ${YELLOW}docker ps${NC}"
echo ""
echo "Container'ları yeniden başlat:"
echo "  ${YELLOW}docker compose restart${NC}"
echo ""
echo "Container'ları durdur:"
echo "  ${YELLOW}docker compose down${NC}"
echo ""
echo "Yeniden build et ve başlat:"
echo "  ${YELLOW}docker compose down${NC}"
echo "  ${YELLOW}docker compose build --no-cache${NC}"
echo "  ${YELLOW}docker compose up -d${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "\n${GREEN}İyi çalışmalar! 🚀${NC}\n"

