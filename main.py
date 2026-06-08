import webview
import os

from data.repository import Repository
from automation.jira_bot import JiraBot
from api.webview_api import WebviewApi

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_FILE = os.path.join(BASE_DIR, 'templates.json')
REQUESTERS_FILE = os.path.join(BASE_DIR, 'requesters.json')
BROWSER_DATA_DIR = os.path.join(BASE_DIR, 'browser_data')

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
