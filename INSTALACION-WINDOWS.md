# Instalación en Windows

Guía para instalar este setup en una PC con Windows. Está escrita para que **Claude Code la
siga paso a paso**: abre `claude` dentro de esta carpeta y dile *"instala mi setup"*.

## Qué se instala

Todo, igual que en la Mac. `install-windows.ps1` copia los archivos tal cual, salvo que en
`office.md`, `settings.json` y los hooks de Gemini cambia `/usr/bin/python3 ~/.claude/` por
`python C:/Users/<usuario>/.claude/`. Esa ruta funciona igual desde Git Bash que desde cmd.

| Pieza | Destino |
|---|---|
| `claude/agents/*.md` | `%USERPROFILE%\.claudegents\` |
| `claude/commands/*.md` (con `/office`) | `%USERPROFILE%\.claude\commands\` |
| `claude/clawd/` (statusline, oficina 3D, `sim-oficina.sh`) | `%USERPROFILE%\.claude\clawd\` |
| `claude/settings.fragment.json` | se combina en `%USERPROFILE%\.claude\settings.json` (con respaldo) |
| `gemini/hooks.json` | se combina en `%USERPROFILE%\.gemini\config\hooks.json`, si existe `.gemini` |

Si no hay Python 3 en el PATH, el instalador solo copia agentes y comandos (sin `/office`)
y no toca `settings.json`; si no, los hooks fallarían en cada evento.

## Pasos (para Claude)

1. **Requisitos.** Comprueba que existan `git --version`, `claude --version` y
   `python --version` (3.8 o más nuevo; para Clawd). Si falta
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
   Copia los agentes, los comandos y Clawd, y combina `settings.json`.

5. **Verificar.** Pídele al usuario que abra una sesión **nueva** de `claude` y:
   - escriba `/agents`: deben aparecer `explorador`, `planificador`, `revisor`,
     `seguridad` y `guia-tdd`;
   - escriba `/`: deben aparecer `/planear`, `/explicar`, `/tdd`, `/revisar-codigo` y
     `/seguridad`;
   - vea a Clawd en la barra de estado y escriba `/office` para abrir la oficina;
   - pruebe en algún proyecto, por ejemplo `/explicar cómo arranca la app`.

6. **Contarle al usuario** qué se copió, qué se respaldó y qué se dejó fuera y por qué.

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
