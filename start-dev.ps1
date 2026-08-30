# Script auxiliar para inicializacao do ambiente de desenvolvimento
param (
    [Parameter(Position = 0)]
    [ValidateSet("all", "backend", "frontend", "test")]
    [string]$Mode = "all"
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# Configura PATH para fnm e uv
$env:Path = "C:\Users\fakef\.local\bin;$env:Path"
if (Get-Command fnm -ErrorAction SilentlyContinue) {
    & fnm env --use-on-cd | Out-String | Invoke-Expression
}

if ($Mode -eq "test") {
    Write-Host "===> Executando testes do Backend..." -ForegroundColor Cyan
    Set-Location "$root\backend"
    & ".\.venv\Scripts\pytest"

    Write-Host "`n===> Executando testes do Frontend..." -ForegroundColor Cyan
    Set-Location "$root\frontend"
    npm test

    Write-Host "`n===> Verificando linting..." -ForegroundColor Cyan
    npm run lint
    Set-Location "$root\backend"
    & ".\.venv\Scripts\ruff" check .
    Set-Location $root
    return
}

if ($Mode -eq "backend" -or $Mode -eq "all") {
    Write-Host "Iniciando Backend na porta 8000..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; & '.\.venv\Scripts\uvicorn' app.main:app --reload --port 8000"
}

if ($Mode -eq "frontend" -or $Mode -eq "all") {
    Write-Host "Iniciando Frontend Vite..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; & 'C:\Users\fakef\.local\bin\fnm.exe' env --use-on-cd | Out-String | Invoke-Expression; npm run dev"
}

Write-Host "Ambiente pronto!" -ForegroundColor Cyan
