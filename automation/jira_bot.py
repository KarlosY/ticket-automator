from playwright.sync_api import sync_playwright

class JiraBot:
    def __init__(self, browser_data_dir, notify_complete_callback=None, notify_error_callback=None):
        self.browser_data_dir = browser_data_dir
        self.notify_complete_callback = notify_complete_callback
        self.notify_error_callback = notify_error_callback

    def run_task(self, template, requester, url, custom_texts_list=None):
        try:
            with sync_playwright() as p:
                print("Starting Playwright...")
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.browser_data_dir,
                    headless=False,
                    args=['--start-maximized'],
                    no_viewport=True
                )
                
                page = context.pages[0] if context.pages else context.new_page()
                
                # Si no hay lista, procesamos una sola vez con los datos originales de la plantilla
                if not custom_texts_list:
                    custom_texts_list = [None]
                
                for idx, text_line in enumerate(custom_texts_list):
                    print(f"Navigating to {url} (Ticket {idx+1}/{len(custom_texts_list)})")
                    page.goto(url)
                    
                    # Crear copia de la plantilla para inyectar el texto si existe
                    current_template = dict(template)
                    if text_line:
                        current_template['summary'] = text_line
                        current_template['details'] = text_line
                        
                    self._execute_jira_automation(page, current_template, requester)
                    
                    # Esperar 10 segundos antes de proceder con el siguiente ticket (salvo que sea el último)
                    if idx < len(custom_texts_list) - 1:
                        print("Waiting 10 seconds before the next ticket...")
                        page.wait_for_timeout(10000)
                
                print("All automations completed. Browser will stay open until you close it.")
                page.wait_for_event("close", timeout=0)
                context.close()
                
                if self.notify_complete_callback:
                    self.notify_complete_callback()
                    
        except Exception as e:
            print("Playwright error:", str(e))
            if self.notify_error_callback:
                self.notify_error_callback(str(e))

    def _execute_jira_automation(self, page, template, requester):
        def get_input_for_label(labels):
            if isinstance(labels, str): labels = [labels]
            for label_text in labels:
                label = page.locator(f"label:has-text('{label_text}')").first
                try:
                    label.wait_for(state="attached", timeout=1500)
                    for_id = label.get_attribute("for")
                    if for_id:
                        input_loc = page.locator(f"#{for_id}").first
                        try:
                            # Validar que el elemento con for_id realmente existe, sino hacer fallback
                            input_loc.wait_for(state="attached", timeout=500)
                            return input_loc
                        except Exception:
                            pass
                except:
                    pass
                
                # Fallback XPath robusto (incluye editores modernos de texto enriquecido)
                fallback_xpath = (
                    f"//*[text()='{label_text}' or contains(text(), '{label_text}')]/following::input[1] | "
                    f"//*[contains(text(), '{label_text}')]/following::textarea[1] | "
                    f"//*[contains(text(), '{label_text}')]/following::*[@contenteditable='true'][1] | "
                    f"//*[contains(text(), '{label_text}')]/following::*[@role='textbox'][1]"
                )
                fallback = page.locator(f"xpath={fallback_xpath}").first
                try:
                    fallback.wait_for(state="attached", timeout=1000)
                    return fallback
                except:
                    pass
            raise Exception(f"Input not found for any of: {labels}")

        def fill_by_label(labels, value):
            if isinstance(labels, str): labels = [labels]
            try:
                locator = get_input_for_label(labels)
                tag = locator.evaluate("el => el.tagName.toLowerCase()")
                is_editable = locator.evaluate("el => el.isContentEditable")
                
                if tag not in ["input", "textarea"] and not is_editable:
                    editor = locator.locator("[contenteditable='true']").first
                    if editor.count() > 0:
                        locator = editor
                    else:
                        inner = locator.locator("input, textarea").first
                        if inner.count() > 0:
                            locator = inner
                            
                locator.wait_for(state="visible", timeout=3000)
                locator.scroll_into_view_if_needed()
                
                if locator.evaluate("el => el.isContentEditable"):
                    locator.click()
                    # Playwright's fill sometimes struggles with ProseMirror, so we clear and type
                    page.keyboard.press("Control+a")
                    page.keyboard.press("Backspace")
                    locator.type(value, delay=10)
                else:
                    locator.fill(value)
                    
                print(f"Filled {labels[0]} with {value}")
            except Exception as e:
                print(f"Could not fill {labels[0]}: {e}")

        def select_dropdown(labels, value, index=0):
            if isinstance(labels, str): labels = [labels]
            
            for label_text in labels:
                try:
                     # 1. Encontrar el texto de la etiqueta
                     label_node = page.locator(f"xpath=//*[text()='{label_text}' or contains(text(), '{label_text}')]").first
                     label_node.wait_for(state="attached", timeout=3000)
                     
                     # 2. Buscar las cajas de texto (inputs) asociadas a este campo.
                     # Buscamos inputs que no estén ocultos dentro del Padre, Abuelo, o siguientes.
                     inputs = label_node.locator("xpath=..//input[not(@type='hidden')]")
                     
                     if inputs.count() <= index:
                         inputs = label_node.locator("xpath=../..//input[not(@type='hidden')]")
                         
                     if inputs.count() <= index:
                         # Fallback: buscar los siguientes inputs visibles en el documento
                         inputs = page.locator(f"xpath=//*[text()='{label_text}' or contains(text(), '{label_text}')]/following::input[not(@type='hidden')]")

                     if inputs.count() > index:
                         cb_input = inputs.nth(index)
                         cb_input.scroll_into_view_if_needed()
                         cb_input.click(force=True)
                         cb_input.fill("")
                         cb_input.type(value, delay=50) # Tipeamos
                         page.wait_for_timeout(1000) # Esperamos 1 segundo
                         page.keyboard.press("Enter") # Seleccionamos
                         print(f"Typed and pressed Enter for {value} in {label_text} (Index {index})")
                         return True
                         
                except Exception as e:
                    print(f"Error acting on {label_text}: {e}")
                    continue
                    
            print(f"Could not find select box for any of: {labels} at index {index}")
            return False

        # 1. Solicitante
        try:
            user_target = get_input_for_label(["Generar esta solicitud en nombre de", "Solicitante", "Raise this request on behalf of"])
            tag = user_target.evaluate("el => el.tagName.toLowerCase()")
            user_input = user_target.locator("input").first if tag not in ["input", "textarea"] else user_target
            
            user_input.wait_for(state="visible", timeout=5000)
            user_input.fill("")
            user_input.type(requester['email'], delay=100)
            page.wait_for_timeout(2500)
            
            user_option = page.locator("div[role='option']").first
            if user_option.is_visible(timeout=3000):
                user_option.click()
            else:
                page.keyboard.press("Enter")
            print("Filled requester")
        except Exception as e:
            print("Could not fill requester:", e)
        
        # 2. Categoría
        select_dropdown(["Categoría de pedido", "Categoría de Incidencia", "Categoría", "Tipo de incidencia"], template.get('category', 'Software'), index=0)
        page.wait_for_timeout(2500) # TIEMPO CRÍTICO: Jira tarda en cargar las subcategorías tras elegir la categoría
        
        if template.get('category_sub'):
            # En incidencias es un campo separado llamado 'Subcategoría' (index=0)
            # En requerimientos es el segundo combo (index=1) bajo 'Categoría de pedido'
            success = select_dropdown(["Subcategoría"], template.get('category_sub'), index=0)
            if not success:
                select_dropdown(["Categoría de pedido", "Categoría de Incidencia"], template.get('category_sub'), index=1)

        # 3. Acción
        select_dropdown(["Acción", "Tipo de acción"], template.get('action', 'Instalación de software'))
        
        # 4. Nombre de software
        if template.get('software_name', '').strip():
            fill_by_label(["Ingresar nombre de software", "Nombre de software", "Software"], template.get('software_name'))
        
        # 5. Resumen
        if template.get('summary', '').strip():
            fill_by_label(["Resumen de la solicitud", "Resumen del incidente", "Resumen", "Summary"], template.get('summary'))
        
        # 6. Detalle
        if template.get('details', '').strip():
            fill_by_label(["Detalle de la solicitud", "Detalle de la incidencia", "Descripción", "Detalles", "Description"], template.get('details'))
                 
        # 7. Número de contacto y Ubicación
        fill_by_label(["Número de contacto", "Teléfono"], "0")
        fill_by_label(["Ubicación del usuario", "Ubicación", "Sede"], "SD Paseo del Bosque")
        
        # 8. Enviar el formulario
        try:
            page.wait_for_timeout(1000) # Pequeña pausa antes de enviar
            submit_btn = page.locator("button:has-text('Enviar'), button:has-text('Create'), button:has-text('Submit'), input[type='submit']").first
            
            if submit_btn.is_visible(timeout=3000):
                # COMENTADO PARA PRUEBAS:
                # submit_btn.click()  
                print("Simulated clicking Enviar button (Test Mode)")
            else:
                print("Could not find the Enviar button")
        except Exception as e:
            print(f"Error clicking Enviar button: {e}")
