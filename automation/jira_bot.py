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
                        return page.locator(f"#{for_id}").first
                except:
                    pass
                
                # Fallback XPath
                fallback = page.locator(f"xpath=//*[text()='{label_text}' or contains(text(), '{label_text}')]/following::input[1] | //*[contains(text(), '{label_text}')]/following::textarea[1]").first
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
                if tag not in ["input", "textarea"]:
                    editor = locator.locator("[contenteditable='true']").first
                    if editor.count() > 0:
                        editor.fill(value)
                        print(f"Filled rich text {labels[0]} with {value}")
                        return
                    inner = locator.locator("input, textarea").first
                    if inner.count() > 0:
                        locator = inner
                        
                locator.wait_for(state="visible", timeout=3000)
                locator.fill(value)
                print(f"Filled {labels[0]} with {value}")
            except Exception as e:
                print(f"Could not fill {labels[0]}: {e}")

        def select_dropdown(labels, value, index=0):
            if isinstance(labels, str): labels = [labels]
            
            for label_text in labels:
                try:
                    # Búsqueda DOM: El n-ésimo input visible DESPUÉS del texto
                    # Esto evita perfectamente agarrar el input del vecino porque respeta el orden del DOM.
                    # Ignoramos el atributo 'for' porque Jira a veces genera IDs duplicados en campos contiguos.
                    xpath = f"(//*[self::label or self::span or self::legend][contains(text(), '{label_text}')])[1]/following::input[not(@type='hidden') and not(@type='checkbox')]"
                    combo = page.locator(f"xpath={xpath}").nth(index)
                    
                    if combo.count() > 0:
                        combo.wait_for(state="attached", timeout=2000)
                        combo.scroll_into_view_if_needed()
                        combo.click(force=True)
                        page.wait_for_timeout(500) # Give React-Select time to open
                        page.keyboard.type(value, delay=50)
                        page.wait_for_timeout(1500) # Tiempo para que React-Select cargue las opciones
                        page.keyboard.press("Enter")
                        print(f"Typed and pressed Enter for {value} in {label_text} via DOM order (Index {index})")
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
                submit_btn.click()  # REACTIVADO PARA CREACIÓN EN LOTE
                print("Clicked Enviar button")
            else:
                print("Could not find the Enviar button")
        except Exception as e:
            print(f"Error clicking Enviar button: {e}")
