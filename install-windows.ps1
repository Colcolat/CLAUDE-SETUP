# Installs this Claude Code setup into ~/.claude on Windows (and Antigravity's hooks
# into ~/.gemini, if Antigravity is there). Safe to run again to update: files that
# change are backed up first (.bak-<date>), and settings.json is merged, never replaced.
# The repo keeps macOS paths; here "/usr/bin/python3 ~/.claude/" becomes
# "python C:/Users/<you>/.claude/", which works from Git Bash and from cmd.
$ErrorActionPreference = 'Stop'

$aqui = $PSScriptRoot
$claude = Join-Path $HOME '.claude'
$sello = Get-Date -Format 'yyyyMMdd-HHmmss'
$utf8 = New-Object System.Text.UTF8Encoding $false  # no BOM: it breaks frontmatter and JSON
$claudeSlash = ($claude -replace '\\', '/') + '/'

function Adaptar($texto) {
    $texto.Replace('/usr/bin/python3 ~/.claude/', "python $claudeSlash")
}

function Leer($ruta) { [IO.File]::ReadAllText($ruta, $utf8) }

# Write text to destino, backing up the old file if it is different.
function Escribir($texto, $destino) {
    New-Item -ItemType Directory -Force -Path (Split-Path $destino) | Out-Null
    if (Test-Path $destino) {
        if ((Leer $destino) -ceq $texto) {
            Write-Host "  sin cambios: $destino"
            return
        }
        Copy-Item $destino "$destino.bak-$sello"
        Write-Host "  respaldo: $destino.bak-$sello"
    }
    [IO.File]::WriteAllText($destino, $texto, $utf8)
    Write-Host "  copiado: $destino"
}

$hayPython = $null -ne (Get-Command python -ErrorAction SilentlyContinue)
if ($hayPython) { python -c "import sys; sys.exit(sys.version_info < (3, 8))"; $hayPython = $? }
if (-not $hayPython) {
    Write-Host 'No encontre python 3: instalo solo agentes y comandos, sin Clawd.'
    Write-Host 'Instala Python desde https://www.python.org/downloads/ y vuelve a correr esto.'
}

foreach ($carpeta in 'agents', 'commands') {
    Write-Host "$carpeta -> $claude\$carpeta"
    Get-ChildItem (Join-Path $aqui "claude\$carpeta") -Filter *.md |
        Where-Object { $hayPython -or $_.Name -ne 'office.md' } |
        ForEach-Object { Escribir (Adaptar (Leer $_.FullName)) (Join-Path $claude "$carpeta\$($_.Name)") }
}

if (-not $hayPython) { return }

Write-Host "clawd -> $claude\clawd"
Get-ChildItem (Join-Path $aqui 'claude\clawd') -File |
    ForEach-Object { Escribir (Leer $_.FullName) (Join-Path $claude "clawd\$($_.Name)") }

# Same merge as install.sh: replace statusline and panel, add env, and add each
# hook only if its command isn't there yet, keeping the user's own hooks.
$combinar = @'
import json, os, shutil, sys

frag_path, path, stamp, mode = sys.argv[1:5]
frag = json.load(open(frag_path, encoding="utf-8"))
s = {}
if os.path.exists(path):
    shutil.copy(path, path + ".bak-" + stamp)
    print("  respaldo: " + path + ".bak-" + stamp)
    s = json.load(open(path, encoding="utf-8"))

if mode == "gemini":
    s.update(frag)  # only replaces our own "clawd-office" hook
else:
    s["statusLine"] = frag["statusLine"]
    s["subagentStatusLine"] = frag["subagentStatusLine"]
    s.setdefault("env", {}).update(frag["env"])
    hooks = s.setdefault("hooks", {})
    for event, groups in frag["hooks"].items():
        mine = hooks.setdefault(event, [])
        have = {h.get("command") for g in mine for h in g.get("hooks", [])}
        for g in groups:
            if any(h.get("command") not in have for h in g.get("hooks", [])):
                mine.append(g)

os.makedirs(os.path.dirname(path), exist_ok=True)
tmp = path + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(s, f, indent=2, ensure_ascii=False)
    f.write("\n")
os.replace(tmp, path)
'@
$tmp = Join-Path ([IO.Path]::GetTempPath()) "claude-setup-$sello"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
[IO.File]::WriteAllText("$tmp\combinar.py", $combinar, $utf8)

Write-Host 'Combinando settings.json...'
[IO.File]::WriteAllText("$tmp\fragment.json", (Adaptar (Leer "$aqui\claude\settings.fragment.json")), $utf8)
python "$tmp\combinar.py" "$tmp\fragment.json" "$claude\settings.json" $sello claude
if (-not $?) { throw 'No pude combinar settings.json' }

if (Test-Path (Join-Path $HOME '.gemini')) {
    Write-Host 'Agregando los hooks de Gemini (Antigravity)...'
    [IO.File]::WriteAllText("$tmp\gemini.json", (Adaptar (Leer "$aqui\gemini\hooks.json")), $utf8)
    python "$tmp\combinar.py" "$tmp\gemini.json" "$HOME\.gemini\config\hooks.json" $sello gemini
    if (-not $?) { throw 'No pude combinar los hooks de Gemini' }
} else {
    Write-Host 'No encontre ~/.gemini: me salto los hooks de Gemini.'
}
Remove-Item -Recurse -Force $tmp

Write-Host ''
Write-Host 'Listo. Abre una sesion nueva de claude para que tome los cambios.'
Write-Host 'Prueba la oficina sin gastar tokens:'
Write-Host "  python ${claudeSlash}clawd/clawd.py office demo-oficina"
Write-Host '  bash ~/.claude/clawd/sim-oficina.sh'
