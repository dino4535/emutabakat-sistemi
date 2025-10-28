@echo off
chcp 65001 > nul
echo.
echo ============================================================
echo E-MUTABAKAT SİSTEMİ - RESTART
echo ============================================================
echo.
echo [1/3] Eski process'leri durduruluyor...
echo.

REM Backend ve frontend process'lerini durdur
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *start_backend*" 2>nul
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *vite*" 2>nul
timeout /t 2 /nobreak > nul

echo [2/3] Backend baslatiliyor...
echo.
start "E-Mutabakat Backend" cmd /k "cd /d %~dp0 && .\venv\Scripts\Activate.ps1 && python start_backend.py"
timeout /t 3 /nobreak > nul

echo [3/3] Frontend baslatiliyor...
echo.
start "E-Mutabakat Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================================
echo [OK] Backend ve Frontend yeniden basladi!
echo ============================================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Kapanmasi icin her iki terminalde CTRL+C basin.
echo.
pause

