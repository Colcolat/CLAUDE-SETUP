# CLAUDE-SETUP

Mi configuración de Claude Code para macOS y Windows: un Clawd animado en el statusline, el panel del
equipo de subagentes, una oficina 3D en el navegador donde se ve a los agentes trabajar y
mandarse mensajes, y mis subagentes y comandos.

## Qué incluye

| Pieza | Dónde queda | Qué hace |
|---|---|---|
| `claude/clawd/clawd.py` | `~/.claude/clawd/` | Statusline con Clawd en pixel art, panel de subagentes, registro de eventos y servidor de la oficina |
| `claude/clawd/office.html` | `~/.claude/clawd/` | La oficina 3D (three.js): cada agente camina a su zona, se mandan sobres, tablero del equipo |
| `claude/clawd/sim-oficina.sh` | `~/.claude/clawd/` | Demo sin gastar tokens (equipo completo, y `--gemini`) |
| `claude/agents/*.md` | `~/.claude/agents/` | Subagentes: explorador, planificador, revisor, seguridad, guia-tdd |
| `claude/commands/*.md` | `~/.claude/commands/` | `/office`, `/planear`, `/explicar`, `/tdd`, `/revisar-codigo`, `/seguridad` |
| `claude/settings.fragment.json` | se combina en `~/.claude/settings.json` | Hooks, statusline, panel de agentes y agent teams activados |
| `gemini/hooks.json` | se combina en `~/.gemini/config/hooks.json` | Para ver a Gemini (Antigravity) en su estudio de la oficina |

Además: [PRACTICAS.md](PRACTICAS.md) (cómo trabajar con estos roles) y
[ejemplos/modelo-dual](ejemplos/modelo-dual) (un `CLAUDE.md` de proyecto y un revisor
especializado que reemplaza al global).

## Instalar en Windows

Todo, Clawd incluido; solo necesitas Python 3 en el PATH (`python --version`). Sigue
[INSTALACION-WINDOWS.md](INSTALACION-WINDOWS.md), o abre `claude` en esta carpeta y dile
*"instala mi setup"*.

## Instalar en otra Mac

Necesitas `/usr/bin/python3`, que viene con las herramientas de línea de comandos de Xcode
(`xcode-select --install`). No hace falta instalar nada más: la oficina carga three.js de un CDN.

```bash
git clone https://github.com/Colcolat/CLAUDE-SETUP.git ~/Documents/CLAUDE-SETUP
cd ~/Documents/CLAUDE-SETUP
./install.sh
```

El instalador:
- copia los archivos y respalda (`.bak-<fecha>`) cualquiera que ya existiera y sea distinto;
- **combina** `settings.json`: agrega mis hooks, el statusline y el panel, y deja intactas tus
  otras opciones y hooks (también lo respalda antes);
- agrega los hooks de Gemini solo si existe `~/.gemini`.

Después abre una sesión nueva de `claude`.

## Probar

```bash
/usr/bin/python3 ~/.claude/clawd/clawd.py office demo-oficina   # abre la oficina
bash ~/.claude/clawd/sim-oficina.sh                             # el equipo completo
bash ~/.claude/clawd/sim-oficina.sh --gemini                    # Gemini en paralelo
```

Dentro de Claude Code: `/office` abre la oficina de la sesión actual. En la oficina, la rueda o
el trackpad hacen zoom hacia el cursor, las flechas mueven la cámara y doble clic en un agente
la centra en él. El servidor solo escucha en `127.0.0.1` y se apaga solo 5 minutos después de
cerrar la última pestaña.

## Actualizar

En esta Mac, después de cambiar algo en `~/.claude`, copia los archivos al repo y súbelos. En
la otra:

```bash
cd ~/Documents/CLAUDE-SETUP && git pull && ./install.sh
```

## Notas

- **Agent teams** quedan activados (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`): gastan bastante
  más tokens. Para apagarlos, pon `"0"` en el `env` de `~/.claude/settings.json`.
- Los subagentes están adaptados de
  [everything-claude-code](https://github.com/affaan-m/everything-claude-code), reescritos para
  detectar el stack de cada proyecto y responder en español.
