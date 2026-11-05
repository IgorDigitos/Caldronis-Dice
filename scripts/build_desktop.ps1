$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectDir '.venv\Scripts\python.exe'
$distPath = Join-Path $projectDir 'dist'
$buildPath = Join-Path $projectDir 'build\desktop'
$entryPath = Join-Path $projectDir 'desktop_app.py'

& $pythonPath -m PyInstaller --noconfirm --onefile --windowed --noupx --name CaldronisDice --distpath $distPath --workpath $buildPath --specpath $buildPath $entryPath
if ($LASTEXITCODE -ne 0) { throw 'Falha ao gerar o executável.' }

$exePath = Join-Path $distPath 'CaldronisDice.exe'
if (-not (Test-Path -LiteralPath $exePath)) { throw 'Executável não encontrado.' }
$desktopPath = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktopPath 'Caldronis Dice.lnk'
$shortcutShell = New-Object -ComObject WScript.Shell
$shortcut = $shortcutShell.CreateShortcut($shortcutPath)
if ((Test-Path -LiteralPath $shortcutPath) -and $shortcut.TargetPath -ne $exePath) {
    throw 'Já existe um atalho com esse nome apontando para outro programa. Ele foi preservado.'
}
$shortcut.TargetPath = $exePath
$shortcut.Arguments = '--project-dir "' + $projectDir + '"'
$shortcut.WorkingDirectory = $projectDir
$shortcut.Description = 'Ligar e desligar o bot Caldronis Dice'
$shortcut.IconLocation = $exePath + ',0'
$shortcut.Save()
Write-Output ('Executável: ' + $exePath)
Write-Output ('Atalho: ' + $shortcutPath)
