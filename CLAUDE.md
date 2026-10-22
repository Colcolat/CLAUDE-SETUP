# CLAUDE-SETUP

Configuración personal de Claude Code: subagentes, comandos y Clawd (statusline, oficina 3D y
hooks), para macOS y Windows. Háblame en español y explica lo que haces en términos sencillos.

## Si te piden instalar o actualizar
- **En Windows:** sigue [INSTALACION-WINDOWS.md](INSTALACION-WINDOWS.md) al pie de la letra.
  `install-windows.ps1` instala todo y cambia `/usr/bin/python3 ~/.claude/` por
  `python C:/Users/<usuario>/.claude/` al copiar. En el repo se quedan las rutas de Mac.
- **En macOS:** sigue la sección "Instalar en otra Mac" del [README](README.md) (`./install.sh`).
- Antes de reemplazar algo en `~/.claude`, mira qué hay y dile al usuario qué se va a respaldar.
- Al terminar, dile qué se copió, qué se respaldó y qué quedó fuera.

## Si te piden cambiar el setup
- Este repo es la copia que viaja entre computadoras; los archivos que Claude usa están en
  `~/.claude/`. Cambia los dos, o copia de uno al otro, para que no se desincronicen.
- Los agentes y comandos deben seguir funcionando en macOS y en Windows: nada de rutas fijas de
  un solo sistema dentro de ellos (salvo `/usr/bin/python3 ~/.claude/`, que el instalador de
  Windows reescribe).
- `clawd.py` corre en los dos: lo propio de cada sistema va detrás de `sys.platform`, y los
  archivos de texto se abren con `encoding="utf-8"`.
- El repo es **público**: nunca subas tokens, `settings.json` completos, historiales
  (`history.jsonl`, `projects/`) ni datos personales.
- Commits con Conventional Commits en inglés (`feat:`, `docs:`, `fix:`).

Buenas prácticas de uso: [PRACTICAS.md](PRACTICAS.md).
