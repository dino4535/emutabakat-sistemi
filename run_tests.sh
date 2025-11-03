#!/bin/bash
# Test Runner Script (Bash)

echo "🧪 E-Mutabakat Testleri Başlatılıyor..."
echo ""

# Python virtual environment kontrolü
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Testleri çalıştır
python -m pytest backend/tests -v --tb=short --color=yes

# Coverage (opsiyonel)
if [ "$1" == "--coverage" ]; then
    echo ""
    echo "📊 Coverage raporu oluşturuluyor..."
    python -m pytest backend/tests --cov=backend --cov-report=html --cov-report=term
    echo "Coverage raporu: htmlcov/index.html"
fi

echo ""
echo "✅ Testler tamamlandı!"

