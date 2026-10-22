# CLAUDE-SETUP

Configuración personal de Claude Code: subagentes, comandos y, solo en macOS, Clawd (statusline,
oficina 3D y hooks). Háblame en español y explica lo que haces en términos sencillos.

## Si te piden instalar o actualizar
- **En Windows:** sigue [INSTALACION-WINDOWS.md](INSTALACION-WINDOWS.md) al pie de la letra.
  Solo se instalan agentes y comandos; nada de Clawd ni cambios a `settings.json`.
- **En macOS:** sigue la sección "Instalar en otra Mac" del [README](README.md) (`./install.sh`).
- Antes de reemplazar algo en `~/.claude`, mira qué hay y dile al usuario qué se va a respaldar.
- Al terminar, dile qué se copió, qué se respaldó y qué quedó fuera.

## Si te piden cambiar el setup
- Este repo es la copia que viaja entre computadoras; los archivos que Claude usa están en
  `~/.claude/`. Cambia los dos, o copia de uno al otro, para que no se desincronicen.
- Los agentes y comandos deben seguir funcionando en macOS y en Windows: nada de rutas fijas de
  un solo sistema dentro de ellos.
- El repo es **público**: nunca subas tokens, `settings.json` completos, historiales
  (`history.jsonl`, `projects/`) ni datos personales.
- Commits con Conventional Commits en inglés (`feat:`, `docs:`, `fix:`).

Buenas prácticas de uso: [PRACTICAS.md](PRACTICAS.md).
