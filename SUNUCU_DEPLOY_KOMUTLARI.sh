#!/bin/bash
# E-Mutabakat Sistemi - Tam Temizlik ve Fresh Deploy
# Tarih: 31 Ekim 2025

echo "=================================================="
echo "🧹 E-MUTABAKAT - TAM TEMİZLİK VE FRESH DEPLOY"
echo "=================================================="
echo ""

# 1. Mevcut dizine git
cd /opt/emutabakat

echo "[1/10] 📦 Mevcut container'ları durdur ve temizle..."
sudo docker-compose down -v --remove-orphans

echo "[2/10] 🗑️  Proje image'larını sil..."
sudo docker rmi -f $(sudo docker images | awk '/emutabakat/ {print $3}') 2>/dev/null || echo "  ℹ️  Silinecek image bulunamadı"

echo "[3/10] 🧹 Docker builder cache temizle..."
sudo docker builder prune -af

echo "[4/10] 🗂️  Kullanılmayan image'ları temizle..."
sudo docker image prune -af

echo "[5/10] 🌐 Kullanılmayan network'leri temizle..."
sudo docker network prune -f

echo "[6/10] 🔄 Docker daemon'ı yeniden başlat..."
sudo systemctl restart docker
sleep 8
echo "  ✅ Docker hazır"

echo "[7/10] 📥 Git'ten son değişiklikleri çek..."
git fetch origin
git reset --hard origin/main
git pull origin main
echo "  ✅ Kod güncel"

echo "[8/10] 📝 .env dosyasını kontrol et..."
if [ ! -f .env ]; then
    echo "  ⚠️  .env dosyası bulunamadı! Oluşturuluyor..."
    cat > .env <<EOL
# SMS Ayarları (Buraya kendi bilgilerinizi girin)
GOLDSMS_USERNAME=your_username_here
GOLDSMS_PASSWORD=your_password_here
GOLDSMS_ORIGINATOR=BERMER
EOL
    echo "  ⚠️  .env dosyası oluşturuldu. Lütfen düzenleyin:"
    echo "     sudo nano .env"
else
    echo "  ✅ .env dosyası mevcut"
fi

# .env'de SMS ayarları var mı kontrol et
if ! grep -q "GOLDSMS_USERNAME" .env; then
    echo "  ⚠️  .env dosyasına SMS ayarları ekleniyor..."
    cat >> .env <<EOL

# SMS Ayarları
GOLDSMS_USERNAME=your_username_here
GOLDSMS_PASSWORD=your_password_here
GOLDSMS_ORIGINATOR=BERMER
EOL
    echo "  ⚠️  SMS ayarları eklendi. Lütfen düzenleyin:"
    echo "     sudo nano .env"
fi

echo "[9/10] 🏗️  Container'ları sıfırdan build et (cache yok)..."
sudo docker-compose build --no-cache
echo "  ✅ Build tamamlandı"

echo "[10/10] 🚀 Servisleri başlat..."
sudo docker-compose up -d

echo ""
echo "=================================================="
echo "✅ DEPLOYMENT TAMAMLANDI"
echo "=================================================="
echo ""

# Servis durumlarını göster
echo "📊 Servis Durumları:"
sudo docker-compose ps

echo ""
echo "🔍 Container Logları (Ctrl+C ile çıkın):"
echo "  Backend:       sudo docker logs -f emutabakat-backend"
echo "  Frontend:      sudo docker logs -f emutabakat-frontend"
echo "  Celery Worker: sudo docker logs -f emutabakat-celery-worker"
echo ""

# Env kontrolü
echo "🔐 Environment Variable Kontrolü:"
echo "  FRONTEND_URL: $(sudo docker exec emutabakat-backend printenv FRONTEND_URL 2>/dev/null || echo '❌ Bulunamadı')"
echo "  GOLDSMS_USERNAME: $(sudo docker exec emutabakat-backend printenv GOLDSMS_USERNAME 2>/dev/null | cut -c1-3)*** (ilk 3 karakter)"
echo "  GOLDSMS_ORIGINATOR: $(sudo docker exec emutabakat-backend printenv GOLDSMS_ORIGINATOR 2>/dev/null || echo '❌ Bulunamadı')"
echo ""

# Son kontroller
echo "🧪 Final Testler:"
echo "  1. Backend Health: curl -s http://localhost:8000/health"
curl -s http://localhost:8000/health && echo "  ✅ Backend çalışıyor" || echo "  ❌ Backend yanıt vermiyor"
echo ""
echo "  2. Frontend: curl -sI http://localhost:3000"
curl -sI http://localhost:3000 | head -n 1 && echo "  ✅ Frontend çalışıyor" || echo "  ❌ Frontend yanıt vermiyor"
echo ""

echo "=================================================="
echo "📋 SONRAKI ADIMLAR:"
echo "=================================================="
echo "1. SMS ayarlarını düzenleyin:"
echo "   sudo nano /opt/emutabakat/.env"
echo ""
echo "2. SMS ayarlarını güncelledikten sonra backend'i restart edin:"
echo "   sudo docker-compose restart backend celery-worker"
echo ""
echo "3. Yeni bir mutabakat göndererek SMS testini yapın"
echo ""
echo "4. Logları takip edin:"
echo "   sudo docker logs -f emutabakat-backend | grep 'SMS\\|GoldSMS'"
echo ""
echo "=================================================="

