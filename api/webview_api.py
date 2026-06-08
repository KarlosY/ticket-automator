import threading

class WebviewApi:
    def __init__(self, repository, bot_factory):
        """
        repository: Maneja los datos.
        bot_factory: Una funcion o clase que crea el bot con los callbacks correctos
        """
        self._repository = repository
        self._bot_factory = bot_factory
        self._window = None

    def set_window(self, window):
        self._window = window

    def get_templates(self):
        return self._repository.get_templates()

    def get_requesters(self):
        return self._repository.get_requesters()

    def save_templates(self, data):
        return self._repository.save_templates(data)

    def save_requesters(self, data):
        return self._repository.save_requesters(data)

    def _notify_complete(self):
        if self._window:
            self._window.evaluate_js("window.notifyAutomationComplete();")

    def _notify_error(self, error_msg):
        if self._window:
            safe_err = str(error_msg).replace("'", "\\'")
            self._window.evaluate_js(f"window.notifyAutomationError('{safe_err}');")

    def start_automation(self, template_id, requester_id, url, custom_text=None):
        print(f"Starting automation for Template {template_id}, Requester {requester_id} at {url}")
        templates = self.get_templates()
        requesters = self.get_requesters()
        
        template_orig = next((t for t in templates if t['id'] == template_id), None)
        requester = next((r for r in requesters if r['id'] == requester_id), None)
        
        if not template_orig or not requester:
            return {"status": "error", "message": "Plantilla o solicitante no encontrado."}
            
        # Parsear el texto en múltiples líneas, eliminando las vacías
        custom_texts_list = []
        if custom_text and custom_text.strip():
            custom_texts_list = [line.strip() for line in custom_text.splitlines() if line.strip()]
            
        bot = self._bot_factory(self._notify_complete, self._notify_error)
        
        # Ejecutar en un thread para no bloquear la GUI
        thread = threading.Thread(target=bot.run_task, args=(template_orig, requester, url, custom_texts_list))
        thread.daemon = True
        thread.start()
        
        return {"status": "success", "message": "Iniciando navegador..."}
