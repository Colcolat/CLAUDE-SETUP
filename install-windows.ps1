# Installs this repo's subagents and slash commands into ~/.claude on Windows.
# Safe to run again to update: a file that changes is backed up first (.bak-<date>).
# Only agents and commands: Clawd (statusline, office, hooks) is macOS-only.
$ErrorActionPreference = 'Stop'

$aqui = $PSScriptRoot
$claude = Join-Path $HOME '.claude'
$sello = Get-Date -Format 'yyyyMMdd-HHmmss'
# These call /usr/bin/python3 and bash, so they don't work on Windows.
$soloMac = @('office.md')

function Copiar($origen, $destino) {
    New-Item -ItemType Directory -Force -Path (Split-Path $destino) | Out-Null
    if (Test-Path $destino) {
        if ((Get-FileHash $origen).Hash -eq (Get-FileHash $destino).Hash) {
            Write-Host "  sin cambios: $destino"
            return
        }
        Copy-Item $destino "$destino.bak-$sello"
        Write-Host "  respaldo: $destino.bak-$sello"
    }
    Copy-Item $origen $destino
    Write-Host "  copiado: $destino"
}

foreach ($carpeta in 'agents', 'commands') {
    Write-Host "$carpeta -> $claude\$carpeta"
    Get-ChildItem (Join-Path $aqui "claude\$carpeta") -Filter *.md |
        Where-Object { $soloMac -notcontains $_.Name } |
        ForEach-Object { Copiar $_.FullName (Join-Path $claude "$carpeta\$($_.Name)") }
}

Write-Host ''
Write-Host 'Listo. Abre una sesion nueva de claude y escribe /agents para ver los subagentes.'
