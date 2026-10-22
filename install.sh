#!/bin/bash
# Installs this Claude Code setup into ~/.claude (and Antigravity's hooks into
# ~/.gemini, if Antigravity is there). Safe to run again to update: files that
# change are backed up first, and settings.json is merged, never replaced.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CLAUDE="$HOME/.claude"
STAMP="$(date +%Y%m%d-%H%M%S)"
PY=/usr/bin/python3

if [ ! -x "$PY" ]; then
  echo "Falta $PY. Instala las herramientas de línea de comandos con: xcode-select --install"
  exit 1
fi

# Copy one file, backing up the old one if it is different.
put() {
  local src="$1" dst="$2"
  mkdir -p "$(dirname "$dst")"
  if [ -f "$dst" ] && ! cmp -s "$src" "$dst"; then
    cp "$dst" "$dst.bak-$STAMP"
    echo "  respaldo: $dst.bak-$STAMP"
  fi
  cp "$src" "$dst"
}

echo "Copiando archivos a $CLAUDE…"
for f in "$HERE"/claude/clawd/*; do put "$f" "$CLAUDE/clawd/$(basename "$f")"; done
for f in "$HERE"/claude/agents/*.md; do put "$f" "$CLAUDE/agents/$(basename "$f")"; done
for f in "$HERE"/claude/commands/*.md; do put "$f" "$CLAUDE/commands/$(basename "$f")"; done
chmod +x "$CLAUDE/clawd/sim-oficina.sh"

echo "Combinando settings.json…"
"$PY" - "$HERE/claude/settings.fragment.json" "$CLAUDE/settings.json" "$STAMP" <<'EOF'
import json, os, shutil, sys

frag_path, path, stamp = sys.argv[1:4]
frag = json.load(open(frag_path))
s = {}
if os.path.exists(path):
    shutil.copy(path, path + ".bak-" + stamp)
    print("  respaldo: " + path + ".bak-" + stamp)
    s = json.load(open(path))

s["statusLine"] = frag["statusLine"]
s["subagentStatusLine"] = frag["subagentStatusLine"]
s.setdefault("env", {}).update(frag["env"])

# Add each hook command only if it isn't there yet; keep the user's own hooks.
hooks = s.setdefault("hooks", {})
for event, groups in frag["hooks"].items():
    mine = hooks.setdefault(event, [])
    have = {h.get("command") for g in mine for h in g.get("hooks", [])}
    for g in groups:
        if any(h.get("command") not in have for h in g.get("hooks", [])):
            mine.append(g)

tmp = path + ".tmp"
with open(tmp, "w") as f:
    json.dump(s, f, indent=2, ensure_ascii=False)
    f.write("\n")
os.replace(tmp, path)
EOF

if [ -d "$HOME/.gemini" ]; then
  echo "Agregando los hooks de Gemini (Antigravity)…"
  "$PY" - "$HERE/gemini/hooks.json" "$HOME/.gemini/config/hooks.json" "$STAMP" <<'EOF'
import json, os, shutil, sys

src, path, stamp = sys.argv[1:4]
os.makedirs(os.path.dirname(path), exist_ok=True)
s = {}
if os.path.exists(path):
    shutil.copy(path, path + ".bak-" + stamp)
    s = json.load(open(path))
s.update(json.load(open(src)))  # only replaces our own "clawd-office" hook
with open(path, "w") as f:
    json.dump(s, f, indent=2)
    f.write("\n")
EOF
else
  echo "No encontré ~/.gemini: me salto los hooks de Gemini (instala Antigravity y vuelve a correr esto)."
fi

echo
echo "Listo. Abre una sesión nueva de claude para que tome los cambios."
echo "Prueba la oficina sin gastar tokens:"
echo "  /usr/bin/python3 ~/.claude/clawd/clawd.py office demo-oficina"
echo "  bash ~/.claude/clawd/sim-oficina.sh"
