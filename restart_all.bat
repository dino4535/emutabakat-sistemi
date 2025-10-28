@echo off
chcp 65001 > nul
color 0E
cls

echo ============================================================
echo    E-MUTABAKAT SİSTEMİ - YENİDEN BAŞLATILIYOR
echo ============================================================
echo.

echo [1/2] Mevcut servisler durduruluyor...
call stop_all.bat
echo.

echo [2/2] Servisler yeniden başlatılıyor...
timeout /t 2 /nobreak > nul
call start_all.bat

