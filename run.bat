@echo off
echo Iniciando Antigravity Ticket Automator...
echo.

:: Comprobar si existe el entorno virtual
if not exist "venv\" (
    echo Creando entorno virtual de Python...
    python -m venv venv
    
    echo Activando entorno e instalando dependencias...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    
    echo Instalando navegadores de Playwright...
    playwright install chromium
) else (
    call venv\Scripts\activate.bat
)

echo.
echo Iniciando la aplicacion...
python main.py

pause
