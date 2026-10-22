# Instalación en Windows

Guía para instalar este setup en una PC con Windows. Está escrita para que **Claude Code la
siga paso a paso**: abre `claude` dentro de esta carpeta y dile *"instala mi setup"*.

## Qué se instala y qué no

| Pieza | ¿En Windows? | Por qué |
|---|---|---|
| `claude/agents/*.md`: explorador, planificador, revisor, seguridad, guia-tdd | ✅ Sí | Son texto; funcionan en cualquier sistema |
| `claude/commands/*.md`: `/planear`, `/explicar`, `/tdd`, `/revisar-codigo`, `/seguridad` | ✅ Sí | Ídem |
| `claude/commands/office.md` (`/office`) | ❌ No | Llama a `/usr/bin/python3` |
| `claude/clawd/` (statusline, oficina 3D, `sim-oficina.sh`) | ❌ No | `clawd.py` usa `fcntl` (no existe en Windows), abre el navegador con `open` y el demo es bash |
| `claude/settings.fragment.json` (hooks, statusline, agent teams) | ❌ No | Todos los comandos apuntan a `/usr/bin/python3 ~/.claude/clawd/...` |
| `gemini/hooks.json` | ❌ No | Depende de `clawd.py` |
| `install.sh` | ❌ No | Es el instalador de macOS; en Windows se usa `install-windows.ps1` |

**No copies nada de Clawd ni modifiques `settings.json` en Windows**: los hooks fallarían en
cada evento de la sesión.

## Pasos (para Claude)

1. **Requisitos.** Comprueba que existan `git --version` y `claude --version`. Si falta
   Claude Code, la instalación oficial en PowerShell es:
   ```powershell
   irm https://claude.ai/install.ps1 | iex
   ```
   Claude Code en Windows usa Git Bash, que viene con
   [Git for Windows](https://git-scm.com/download/win).

2. **Clonar o actualizar el repo** (si ya estás dentro de él, solo `git pull`):
   ```powershell
   git clone https://github.com/Colcolat/CLAUDE-SETUP.git "$HOME\Documents\CLAUDE-SETUP"
   cd "$HOME\Documents\CLAUDE-SETUP"
   ```

3. **Revisar qué hay antes de copiar.** Lista `$HOME\.claude\agents` y
   `$HOME\.claude\commands`. Si ya existe un archivo con el mismo nombre y es distinto,
   avísale al usuario: el instalador lo respalda como `.bak-<fecha>` antes de reemplazarlo.

4. **Instalar.** Lee `install-windows.ps1` (es corto) y ejecútalo:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install-windows.ps1
   ```
   Copia los 5 agentes y 5 comandos a `$HOME\.claude\`, sin `office.md`.

5. **Verificar.** Pídele al usuario que abra una sesión **nueva** de `claude` y:
   - escriba `/agents`: deben aparecer `explorador`, `planificador`, `revisor`,
     `seguridad` y `guia-tdd`;
   - escriba `/`: deben aparecer `/planear`, `/explicar`, `/tdd`, `/revisar-codigo` y
     `/seguridad`;
   - pruebe en algún proyecto, por ejemplo `/explicar cómo arranca la app`.

6. **Contarle al usuario** qué se copió, qué se respaldó y qué se dejó fuera (Clawd) y por qué.

## Cosas de Windows que conviene saber

- El Python de un entorno virtual está en `.venv\Scripts\python.exe` (en Mac,
  `.venv/bin/python`). Los agentes ya lo saben; si un proyecto tiene `CLAUDE.md` con rutas de
  Mac, adáptalas en esa PC.
- En CEREBRO, `/revisar` es la revisión del wiki; el revisor de código es `/revisar-codigo`.
- Un proyecto puede tener su propio `revisor` en `.claude/agents/revisor.md`, que reemplaza
  al global. Ejemplo en [ejemplos/modelo-dual](ejemplos/modelo-dual).

## Actualizar

Cuando cambie algo en la Mac y se suba al repo:
```powershell
cd "$HOME\Documents\CLAUDE-SETUP"
git pull
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1
```
