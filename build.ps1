$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$iconPath = Join-Path $projectRoot "src\almacen\assets\app_icon.ico"
$pngPath = Join-Path $projectRoot "src\almacen\assets\app_icon.png"

pyinstaller `
  --noconsole `
  --onefile `
  --name "Almacen Informatico" `
  --icon $iconPath `
  --add-data "${pngPath};assets" `
  --add-data "${iconPath};assets" `
  app.py
