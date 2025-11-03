# PowerShell Test Runner Script
# Windows için test çalıştırma scripti

Write-Host "🧪 E-Mutabakat Testleri Başlatılıyor..." -ForegroundColor Cyan
Write-Host ""

# Python virtual environment kontrolü
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Virtual environment aktif ediliyor..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
}

# Testleri çalıştır
Write-Host "Testler çalıştırılıyor..." -ForegroundColor Green
python -m pytest backend/tests -v --tb=short --color=yes

# Coverage (opsiyonel)
if ($args -contains "--coverage") {
    Write-Host ""
    Write-Host "📊 Coverage raporu oluşturuluyor..." -ForegroundColor Yellow
    python -m pytest backend/tests --cov=backend --cov-report=html --cov-report=term
    Write-Host "Coverage raporu: htmlcov\index.html" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ Testler tamamlandı!" -ForegroundColor Green

