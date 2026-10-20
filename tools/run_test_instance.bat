@echo off
rem Lanceur de TEST : sauvegarde temporaire isolee (miaous coupes), la vraie sauvegarde n est pas touchee.
cd /d "%~dp0.."
set "APPDATA=%TEMP%\desktopcat_test"
if not exist "%APPDATA%\DesktopCat" mkdir "%APPDATA%\DesktopCat"
rem 50 croquettes et un chat affame (humeur 20) : de quoi tester le repas tout de suite.
echo {"fish":50,"mood":20,"settings":{"meows":false,"notifications":false}}> "%APPDATA%\DesktopCat\save.json"
rem Le Python du .venv du projet en priorite (c est lui qui a PySide6), sinon celui de Windows.
set "PYW=%CD%\.venv\Scripts\pythonw.exe"
if not exist "%PYW%" set "PYW=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
if not exist "%PYW%" set "PYW=pythonw"
start "" "%PYW%" main.py
