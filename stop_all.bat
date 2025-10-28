@echo off
chcp 65001 > nul
color 0C
cls

echo ============================================================
echo    E-MUTABAKAT SİSTEMİ - TÜM SERVİSLER DURDURULUYOR
echo ============================================================
echo.

echo [1/3] Python işlemleri durduruluyor...
powershell -Command "Get-Process | Where-Object {$_.Path -like '*python*' -and $_.Path -like '*Proje1*'} | ForEach-Object { Write-Host '[DURDURULDU]' $_.Name '(PID:' $_.Id ')'; $_ } | Stop-Process -Force -ErrorAction SilentlyContinue"
timeout /t 1 /nobreak > nul
echo [OK] Python işlemleri durduruldu
echo.

echo [2/3] Node.js işlemleri durduruluyor...
powershell -Command "Get-Process | Where-Object {$_.ProcessName -eq 'node'} | ForEach-Object { Write-Host '[DURDURULDU]' $_.Name '(PID:' $_.Id ')'; $_ } | Stop-Process -Force -ErrorAction SilentlyContinue"
timeout /t 1 /nobreak > nul
echo [OK] Node.js işlemleri durduruldu
echo.

echo [3/3] Port kontrolü yapılıyor...
netstat -ano | findstr ":8000 :5173" > nul 2>&1
if %errorlevel% equ 0 (
    echo [UYARI] Bazı portlar hala kullanımda olabilir
    echo.
    echo Aktif portlar:
    netstat -ano | findstr ":8000 :5173"
) else (
    echo [OK] Tüm portlar serbest
)

echo.
echo ============================================================
echo    TÜM SERVİSLER DURDURULDU!
echo ============================================================
echo.
pause

