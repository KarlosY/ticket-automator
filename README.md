# Antigravity Ticket Automator

Una moderna y potente aplicación de escritorio diseñada para automatizar la creación de tickets repetitivos en plataformas de Mesa de Ayuda como Jira Service Management. Construida con Python, Playwright y una interfaz web vanguardista (PyWebView).

## Arquitectura (Clean Architecture)

El proyecto está diseñado bajo los principios de Clean Architecture para garantizar escalabilidad:

- **`data/` (Capa de Acceso a Datos):** Contiene `repository.py`, encargado de manejar la persistencia de las plantillas y solicitantes en formato JSON.
- **`automation/` (Capa de Infraestructura):** Contiene `jira_bot.py`, el cerebro de Playwright que se encarga de automatizar el navegador de forma robusta e inteligente (maneja Selects en Cascada y componentes React complejos).
- **`api/` (Capa de Presentación):** Contiene `webview_api.py`, la interfaz que conecta el backend de Python con el frontend de JavaScript.
- **`gui/` (Capa de Vista):** Contiene el frontend de la aplicación construido con HTML, CSS (Glassmorphism & Diseño Responsivo) y JavaScript puro.
- **`main.py`:** El punto de entrada que inyecta las dependencias y lanza la aplicación.

## Características Principales

- **Automatización Silenciosa:** Selecciona una plantilla y el bot llenará todo el formulario de Jira de manera automática.
- **Creación en Lotes (Batch Processing):** Sube un archivo `.txt` con una lista de descripciones y el bot creará automáticamente un ticket nuevo para cada línea, con pausas inteligentes de 10 segundos entre cada envío.
- **Modo Oscuro Premium:** Interfaz de usuario diseñada con estética "Glassmorphism", animaciones suaves y una paleta de colores vibrantes.
- **Diseño Responsivo:** La aplicación se adapta automáticamente a diferentes tamaños de pantalla y ventanas.
- **Gestión de Plantillas:** Sistema CRUD integrado para guardar, editar y eliminar tickets frecuentes.
- **Persistencia de Sesión:** Playwright almacena el estado de inicio de sesión, evitando tener que introducir la contraseña repetidamente.

## Uso

1. Ejecuta el archivo `run.bat` (o directamente `python main.py`).
2. Ve a la pestaña **Plantillas** y crea o edita tu ticket repetitivo.
3. En el **Dashboard**, selecciona el Tipo de Solicitud, la plantilla base y el solicitante.
4. *(Opcional)* Si quieres crear muchos tickets de golpe, carga un archivo `.txt` en el botón designado. El bot ignorará el resumen de la plantilla y creará un ticket por cada línea del archivo.
5. Presiona **Iniciar Automatización**. El bot abrirá Chromium, completará los datos y, si usaste un archivo `.txt`, enviará todos los tickets en lote automáticamente con pausas seguras.
