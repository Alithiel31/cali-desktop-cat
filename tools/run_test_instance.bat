@echo off
rem Lanceur de TEST : sauvegarde temporaire isolee (miaous coupes), la vraie sauvegarde n est pas touchee.
cd /d "%~dp0.."
set "APPDATA=%TEMP%\desktopcat_test"
if not exist "%APPDATA%\DesktopCat" mkdir "%APPDATA%\DesktopCat"
echo {"settings":{"meows":false,"notifications":false}}> "%APPDATA%\DesktopCat\save.json"
set "PYW=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
if not exist "%PYW%" set "PYW=pythonw"
start "" "%PYW%" main.py
