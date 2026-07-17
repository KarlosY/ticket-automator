@echo off
echo Preparando entorno para PyInstaller...
set PLAYWRIGHT_BROWSERS_PATH=0

echo Descargando Chromium local (si no existe)...
.\venv\Scripts\playwright.exe install chromium

echo Empaquetando la aplicacion...
.\venv\Scripts\pyinstaller.exe --noconfirm --onedir --windowed --add-data "gui;gui/" --name "TicketAutomator" main.py

echo.
echo Proceso terminado con exito.
echo Tu aplicacion esta en la carpeta: dist\TicketAutomator\
pause
