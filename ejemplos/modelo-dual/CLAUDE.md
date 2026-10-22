# Modelo Dual

App de escritorio (macOS) que arma las minutas semanales y el portafolio de evidencias del
Plan de Formación Dual a partir de la bitácora, Azure DevOps, Jira y Google Chat. El README
explica el uso; este archivo es para trabajar en el código.

## Cómo trabajar conmigo
- Háblame en español y explica lo que haces en términos sencillos: estoy aprendiendo.
- Antes de un cambio grande, propón un plan corto y espera mi visto bueno.
- Después de escribir o modificar código, pasa el subagente `revisor` (.claude/agents/revisor.md)
  y corrige lo que encuentre antes de darme el trabajo por terminado.

## Comandos
```bash
.venv/bin/python -m app.main              # ventana de escritorio
.venv/bin/python -m app.main --web        # en el navegador, http://localhost:8080
.venv/bin/python -m unittest discover tests
```
Usa siempre `.venv/bin/python`, nunca el `python3` del sistema. Para ver la app desde Claude
está la configuración `modelo-dual-web` en `.claude/launch.json`.

## Estructura
- `core/`: lógica sin interfaz. Todo lo que se pueda probar va aquí.
  - `semana.py`: la semana (un JSON en `datos/semanas/AAAA-Wnn.json`) es la unidad de trabajo;
    alimenta la minuta y el portafolio.
  - `bitacora.py`: bitácora en Markdown por mes, más borradores que se guardan en cada tecla.
  - `fuentes/`: Azure DevOps, Jira y Google Chat. Solo leen; nunca escriben en esos servicios.
  - `censura.py` y `evidencias.py`: OCR de macOS para tapar datos sensibles en capturas.
  - `redaccion.py`: llama a `claude -p` sin herramientas, desde una carpeta temporal vacía.
  - `documentos.py`: llena las plantillas Word (docxtpl) y las pasa a PDF con Microsoft Word.
  - `config.py`: rutas, `config.yaml`, `.env` y `escribir_seguro`.
- `app/`: interfaz con NiceGUI. `app/paginas/` tiene una pestaña por archivo y `app/comun.py`
  las piezas compartidas.
- `scripts/`: tareas de una sola vez (crear el .app, las plantillas, importar septiembre).
- `prompts/`: instrucciones y ejemplos que usa `redaccion.py`.

## Datos sensibles (reglas firmes)
- `datos/` y `.env` tienen información real: tokens, nombres, capturas de la empresa y mi firma.
  Están fuera de git y así deben seguir. No los leas ni muestres su contenido salvo que te lo
  pida; para pruebas usa carpetas temporales con `mock.patch`, como en `tests/test_bitacora.py`.
- Las capturas sin censurar (`datos/evidencias/*/originales/`) nunca pueden llegar al
  portafolio, a la minuta, al prompt de Claude ni a git.
- Las conversaciones pegadas se censuran al guardarse (`censura.anonimizar_chat` y
  `tapar_texto`), y el prompt de redacción le pide a Claude no citar `censura.palabras`. Si
  agregas otra fuente de texto ajeno (chats, capturas, comentarios) que llegue al prompt o a un
  documento, pásala por `censura` antes.
- No agregues dependencias que manden datos fuera del equipo (el OCR es local a propósito).

## Convenciones
- Código, nombres, comentarios, mensajes de la interfaz y commits en español.
- Para escribir archivos de datos o configuración usa `config.escribir_seguro`, nunca
  `write_text` ni `open(..., "w")`: la app guarda en cada tecla y un cierre a la mitad no debe
  dejar archivos vacíos.
- El trabajo lento o de red dentro de la interfaz va con `await run.io_bound(...)` para no
  congelar la ventana; las llamadas con `requests` llevan `timeout`.
- Las pruebas usan `unittest` (no pytest) y van en `tests/test_<módulo>.py`.
- Commits: título corto en español y, si hace falta, viñetas con el porqué.
