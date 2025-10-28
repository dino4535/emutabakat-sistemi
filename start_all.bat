@echo off
chcp 65001 > nul
color 0A
cls

echo ============================================================
echo    E-MUTABAKAT SİSTEMİ - TÜM SERVİSLER BAŞLATILIYOR
echo ============================================================
echo.

REM Mevcut Python işlemlerini durdur
echo [1/5] Mevcut Python işlemleri durduruluyor...
powershell -Command "Get-Process | Where-Object {$_.Path -like '*python*' -and $_.Path -like '*Proje1*'} | Stop-Process -Force -ErrorAction SilentlyContinue"
timeout /t 2 /nobreak > nul
echo [OK] Python işlemleri durduruldu
echo.

REM Mevcut Node.js işlemlerini durdur
echo [2/5] Mevcut Node.js işlemleri durduruluyor...
powershell -Command "Get-Process | Where-Object {$_.ProcessName -eq 'node'} | Stop-Process -Force -ErrorAction SilentlyContinue"
timeout /t 2 /nobreak > nul
echo [OK] Node.js işlemleri durduruldu
echo.

REM Backend'i başlat (arka planda)
echo [3/5] Backend başlatılıyor...
start "E-Mutabakat Backend" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && python start_backend.py"
timeout /t 3 /nobreak > nul
echo [OK] Backend başlatıldı
echo.

REM Frontend'i başlat (arka planda)
echo [4/5] Frontend başlatılıyor...
cd frontend
start "E-Mutabakat Frontend" cmd /k "npm run dev"
cd ..
timeout /t 3 /nobreak > nul
echo [OK] Frontend başlatıldı
echo.

echo [5/5] Tüm servisler başlatıldı!
echo ============================================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo API Docs: http://localhost:8000/docs
echo Health:   http://localhost:8000/health
echo.
echo ============================================================
echo.
echo Her iki pencereyi kapatmak için bu pencereyi kapatabilirsiniz.
echo Sadece bu pencereyi kapatmak serisleri durdurmaz!
echo Backend ve Frontend pencerelerini ayrı ayrı kapatmanız gerekir.
echo.
pause

