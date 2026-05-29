import webview
import json
import os
import threading
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_FILE = os.path.join(BASE_DIR, 'templates.json')
REQUESTERS_FILE = os.path.join(BASE_DIR, 'requesters.json')
BROWSER_DATA_DIR = os.path.join(BASE_DIR, 'browser_data')

class Api:
    def get_templates(self):
        if os.path.exists(TEMPLATES_FILE):
            with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def get_requesters(self):
        if os.path.exists(REQUESTERS_FILE):
            with open(REQUESTERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_templates(self, data):
        with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True

    def save_requesters(self, data):
        with open(REQUESTERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True

    def run_playwright_task(self, template, requester, url):
        try:
            with sync_playwright() as p:
                print("Starting Playwright...")
                # Lanza el navegador usando datos persistentes para mantener el login
                context = p.chromium.launch_persistent_context(
                    user_data_dir=BROWSER_DATA_DIR,
                    headless=False,
                    args=['--start-maximized'],
                    no_viewport=True
                )
                
                page = context.pages[0] if context.pages else context.new_page()
                print(f"Navigating to {url}")
                page.goto(url)
                
                def get_input_for_label(label_text):
                    # 1. Buscamos el label exacto o que contenga el texto
                    label = page.locator(f"label:has-text('{label_text}')").first
                    try:
                        label.wait_for(state="attached", timeout=3000)
                        for_id = label.get_attribute("for")
                        if for_id:
                            # Retornamos el elemento con ese ID (Jira asocia el ID al contenedor del React-Select o al input real)
                            return page.locator(f"#{for_id}").first
                    except:
                        pass
                    
                    # 2. Fallback: buscar el siguiente input o textarea en el DOM
                    return page.locator(f"xpath=//*[contains(text(), '{label_text}')]/following::input[1] | //*[contains(text(), '{label_text}')]/following::textarea[1]").first

                def fill_by_label(label_text, value):
                    try:
                        locator = get_input_for_label(label_text)
                        tag = locator.evaluate("el => el.tagName.toLowerCase()")
                        if tag not in ["input", "textarea"]:
                            # Soporte para Rich Text Editor (Jira usa div contenteditable)
                            editor = locator.locator("[contenteditable='true']").first
                            if editor.count() > 0:
                                editor.fill(value)
                                print(f"Filled rich text {label_text} with {value}")
                                return
                                
                            # Soporte para inputs dentro del wrapper
                            inner = locator.locator("input, textarea").first
                            if inner.count() > 0:
                                locator = inner
                                
                        locator.wait_for(state="visible", timeout=5000)
                        locator.fill(value)
                        print(f"Filled {label_text} with {value}")
                    except Exception as e:
                        print(f"Could not fill {label_text}: {e}")

                def select_dropdown(label_text, value, index=0):
                    try:
                         # 1. Encontrar el texto de la etiqueta
                         label_node = page.locator(f"xpath=//*[text()='{label_text}' or contains(text(), '{label_text}')]").first
                         label_node.wait_for(state="attached", timeout=3000)
                         
                         # 2. Buscar las cajas de texto (inputs) asociadas a este campo.
                         # Buscamos inputs que no estén ocultos dentro del Padre, Abuelo, o siguientes.
                         # Esto es clave para selects en cascada donde hay 2 inputs bajo 1 solo label.
                         inputs = label_node.locator("xpath=..//input[not(@type='hidden')]")
                         
                         if inputs.count() <= index:
                             inputs = label_node.locator("xpath=../..//input[not(@type='hidden')]")
                             
                         if inputs.count() <= index:
                             # Fallback: buscar los siguientes inputs visibles en el documento
                             inputs = page.locator(f"xpath=//*[text()='{label_text}' or contains(text(), '{label_text}')]/following::input[not(@type='hidden')]")

                         if inputs.count() > index:
                             cb_input = inputs.nth(index)
                             cb_input.click(force=True)
                             cb_input.fill("")
                             cb_input.type(value, delay=50) # Tipeamos
                             page.wait_for_timeout(1000) # Esperamos 1 segundo
                             page.keyboard.press("Enter") # Seleccionamos
                             print(f"Typed and pressed Enter for {value} in {label_text} (Index {index})")
                         else:
                             print(f"Could not find input box for {label_text} at index {index}")
                             
                    except Exception as e:
                        print(f"Could not select {label_text}: {e}")
                
                # Intentamos rellenar los datos
                # 1. Solicitante (En Jira es un "User Picker" asíncrono)
                try:
                    user_target = get_input_for_label("Generar esta solicitud en nombre de")
                    tag = user_target.evaluate("el => el.tagName.toLowerCase()")
                    user_input = user_target.locator("input").first if tag not in ["input", "textarea"] else user_target
                    
                    user_input.wait_for(state="visible", timeout=5000)
                    user_input.fill("")
                    user_input.type(requester['email'], delay=100) # Tipear lentamente para detonar la API de Jira
                    
                    page.wait_for_timeout(2500) # Esperar a que Jira busque el usuario
                    
                    # Intentamos hacer click en la primera opción de usuario devuelta por la API
                    user_option = page.locator("div[role='option']").first
                    if user_option.is_visible(timeout=3000):
                        user_option.click()
                    else:
                        page.keyboard.press("Enter")
                    print("Filled requester")
                except Exception as e:
                    print("Could not fill requester:", e)
                
                # 2. Categoría (Cascading Select en Jira usa el mismo Label pero son 2 comboboxes)
                select_dropdown("Categoría de pedido", template.get('category', 'Software'), index=0)
                page.wait_for_timeout(500)
                
                # Si hay subcategoría
                if template.get('category_sub'):
                    # En Jira Service Desk, la subcategoría es el SEGUNDO combobox (index=1) bajo el mismo label
                    select_dropdown("Categoría de pedido", template.get('category_sub'), index=1)

                # 3. Acción
                select_dropdown("Acción", template.get('action', 'Instalación de software'))
                
                # 4. Nombre de software
                if template.get('software_name', '').strip():
                    fill_by_label("Ingresar nombre de software", template.get('software_name'))
                
                # 5. Resumen
                if template.get('summary', '').strip():
                    fill_by_label("Resumen de la solicitud", template.get('summary'))
                
                # 6. Detalle (Jira usa contenteditable Prosemirror)
                if template.get('details', '').strip():
                    fill_by_label("Detalle de la solicitud", template.get('details'))
                         
                # 7. Número de contacto y Ubicación
                fill_by_label("Número de contacto", "0")
                fill_by_label("Ubicación del usuario", "SD Paseo del Bosque")
                
                print("Automation completed. Browser will stay open until you close it.")
                # Dejamos el contexto abierto para que el usuario pueda enviar el formulario
                page.wait_for_event("close", timeout=0)
                context.close()
                if len(webview.windows) > 0:
                    webview.windows[0].evaluate_js("window.notifyAutomationComplete();")
        except Exception as e:
            print("Playwright error:", str(e))
            if len(webview.windows) > 0:
                # Need to escape strings
                safe_err = str(e).replace("'", "\\'")
                webview.windows[0].evaluate_js(f"window.notifyAutomationError('{safe_err}');")

    def start_automation(self, template_id, requester_id, url):
        print(f"Starting automation for Template {template_id}, Requester {requester_id} at {url}")
        templates = self.get_templates()
        requesters = self.get_requesters()
        
        template = next((t for t in templates if t['id'] == template_id), None)
        requester = next((r for r in requesters if r['id'] == requester_id), None)
        
        if not template or not requester:
            return {"status": "error", "message": "Plantilla o solicitante no encontrado."}
            
        # Ejecutar en un thread para no bloquear la GUI
        thread = threading.Thread(target=self.run_playwright_task, args=(template, requester, url))
        thread.daemon = True
        thread.start()
        
        return {"status": "success", "message": "Iniciando navegador..."}

if __name__ == '__main__':
    api = Api()
    html_path = os.path.join(BASE_DIR, 'gui', 'index.html')
    # Create window
    window = webview.create_window(
        'Antigravity Ticket Automator', 
        url=html_path, 
        js_api=api,
        width=1000, 
        height=700,
        background_color='#0e111a'
    )
    webview.start(debug=True)
