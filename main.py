import webview
import os

from data.repository import Repository
from automation.jira_bot import JiraBot
from api.webview_api import WebviewApi

import sys
import shutil

# Manejo de rutas para PyInstaller
if getattr(sys, 'frozen', False):
    # Si estamos ejecutando el .exe compilado
    BASE_DIR = sys._MEIPASS
else:
    # Si estamos ejecutando el script normal
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directorio de datos de la aplicación en ProgramData (para persistencia)
PROGRAM_DATA = os.environ.get('PROGRAMDATA', 'C:\\ProgramData')
APP_DATA_DIR = os.path.join(PROGRAM_DATA, 'TicketAutomator')
os.makedirs(APP_DATA_DIR, exist_ok=True)

TEMPLATES_FILE = os.path.join(APP_DATA_DIR, 'templates.json')
REQUESTERS_FILE = os.path.join(APP_DATA_DIR, 'requesters.json')
BROWSER_DATA_DIR = os.path.join(APP_DATA_DIR, 'browser_data')

# Copiar archivos base si es la primera vez que se ejecuta
for file_name in ['templates.json', 'requesters.json']:
    src_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    dst_file = os.path.join(APP_DATA_DIR, file_name)
    if not os.path.exists(dst_file) and os.path.exists(src_file):
        shutil.copy2(src_file, dst_file)

def create_bot(on_complete, on_error):
    return JiraBot(
        browser_data_dir=BROWSER_DATA_DIR,
        notify_complete_callback=on_complete,
        notify_error_callback=on_error
    )

if __name__ == '__main__':
    # 1. Configurar Repositorio (Capa de Datos)
    repository = Repository(TEMPLATES_FILE, REQUESTERS_FILE)
    
    # 2. Configurar API (Capa de Presentación / Controladores)
    api = WebviewApi(repository, bot_factory=create_bot)
    
    # 3. Lanzar Ventana (Framework UI)
    html_path = os.path.join(BASE_DIR, 'gui', 'index.html')
    window = webview.create_window(
        'Antigravity Ticket Automator', 
        url=html_path, 
        js_api=api,
        width=1000, 
        height=700,
        background_color='#0e111a'
    )
    api.set_window(window)
    
    webview.start(debug=True)
