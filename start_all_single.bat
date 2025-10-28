@echo off
chcp 65001 > nul
color 0A
cls

echo ============================================================
echo    E-MUTABAKAT SİSTEMİ - TÜM SERVİSLER BAŞLATILIYOR
echo    (TEK PENCERE MODU)
echo ============================================================
echo.

REM Mevcut işlemleri durdur
echo [1/4] Mevcut işlemler durduruluyor...
powershell -Command "Get-Process | Where-Object {$_.Path -like '*python*' -and $_.Path -like '*Proje1*'} | Stop-Process -Force -ErrorAction SilentlyContinue; Get-Process | Where-Object {$_.ProcessName -eq 'node'} | Stop-Process -Force -ErrorAction SilentlyContinue"
timeout /t 2 /nobreak > nul
echo [OK] Eski işlemler durduruldu
echo.

REM Log dizinini oluştur
if not exist "logs" mkdir logs
set LOG_DATE=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set LOG_DATE=%LOG_DATE: =0%

echo [2/4] Backend başlatılıyor...
start /B cmd /c "call venv\Scripts\activate.bat && python start_backend.py > logs\backend_%LOG_DATE%.log 2>&1"
timeout /t 3 /nobreak > nul
echo [OK] Backend başlatıldı
echo.

echo [3/4] Frontend başlatılıyor...
cd frontend
start /B cmd /c "npm run dev > ..\logs\frontend_%LOG_DATE%.log 2>&1"
cd ..
timeout /t 3 /nobreak > nul
echo [OK] Frontend başlatıldı
echo.

echo [4/4] Servisler kontrol ediliyor...
timeout /t 5 /nobreak > nul

REM Backend kontrolü
curl -s http://localhost:8000/health > nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend hazır: http://localhost:8000
) else (
    echo [HATA] Backend başlatılamadı! Log: logs\backend_%LOG_DATE%.log
)

REM Frontend kontrolü (basit port kontrolü)
netstat -an | findstr ":5173" > nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Frontend hazır: http://localhost:5173
) else (
    echo [HATA] Frontend başlatılamadı! Log: logs\frontend_%LOG_DATE%.log
)

echo.
echo ============================================================
echo    TÜM SERVİSLER BAŞLATILDI!
echo ============================================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo Health:   http://localhost:8000/health
echo.
echo Loglar: logs\ dizininde
echo.
echo UYARI: Bu pencereyi kapatmak servisleri DURDURACAKTIR!
echo Servisleri durdurmak için herhangi bir tuşa basın...
echo.
pause > nul

echo.
echo Servisler durduruluyor...
powershell -Command "Get-Process | Where-Object {$_.Path -like '*python*' -and $_.Path -like '*Proje1*'} | Stop-Process -Force -ErrorAction SilentlyContinue; Get-Process | Where-Object {$_.ProcessName -eq 'node'} | Stop-Process -Force -ErrorAction SilentlyContinue"
timeout /t 2 /nobreak > nul
echo [OK] Tüm servisler durduruldu.
echo.
pause

