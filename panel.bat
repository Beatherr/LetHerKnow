@echo off
title Bot ve Client Yonetim Paneli
cd /d "%~dp0"

:MENU
cls
echo ===================================================
echo               BOT VE CLIENT YONETIM PANELI
echo ===================================================
echo.
echo  [1] Bot ve Client'i Baslat
echo  [2] Bot ve Client'i Durdur
echo  [3] Bilgisayari Kapat (Discord Bildirimi ile)
echo  [4] Paneli Kapat
echo ===================================================
echo.
set /p secim="Seciminizi yapin (1-4): "

if "%secim%"=="1" goto START_ALL
if "%secim%"=="2" goto STOP_ALL
if "%secim%"=="3" goto SHUTDOWN_PC
if "%secim%"=="4" exit
goto MENU

:START_ALL
echo Servisler baslatiliyor...
start "" pythonw.exe bot.py
start "" pythonw.exe client.py
timeout /t 2 >nul
goto MENU

:STOP_ALL
echo Servisler kapatiliyor ve Discord bildirimi gonderiliyor...
powershell -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:8765/activity' -Method Post -Headers @{'X-Activity-Key'='01171120'} -Body '{\"online\": false}' -ContentType 'application/json' -TimeoutSec 3 } catch {}"
timeout /t 2 >nul
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
goto MENU

:SHUTDOWN_PC
cls
echo Discord bildirim istegi gonderiliyor...
powershell -Command "try { $res = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/shutdown' -Method Post -TimeoutSec 5; Write-Output $res } catch { $_.Exception.Message }"
echo.
echo Discord mesaji guncelleniyor, lutfen bekleyin...
timeout /t 5 >nul
echo.
echo Bilgisayar kapatiliyor!
shutdown /s /f /t 5
exit