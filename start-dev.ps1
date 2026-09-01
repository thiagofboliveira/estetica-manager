# Script auxiliar para inicializacao do ambiente de desenvolvimento
param (
    [Parameter(Position = 0)]
    [ValidateSet("all", "backend", "frontend", "test", "db")]
    [string]$Mode = "all"
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# Configura PATH para fnm e uv
$env:Path = "C:\Users\fakef\.local\bin;$env:Path"
if (Get-Command fnm -ErrorAction SilentlyContinue) {
    & fnm env --use-on-cd | Out-String | Invoke-Expression
}

function Start-PostgresIfStopped {
    $pgPortOpen = Get-NetTCPConnection -LocalPort 5432 -State Listen -ErrorAction SilentlyContinue
    if (-not $pgPortOpen) {
        Write-Host "Iniciando PostgreSQL na porta 5432..." -ForegroundColor Cyan
        $pg_bin = "$root\.pg_portable\pgsql\bin"
        $pg_data = "$root\.pg_portable\pgsql\data"
        $pg_log = "$root\.pg_portable\pgsql\logfile.log"
        if (Test-Path "$pg_bin\pg_ctl.exe") {
            & "$pg_bin\pg_ctl.exe" -D $pg_data -l $pg_log -o "-p 5432" start
        }
    } else {
        Write-Host "PostgreSQL ja esta em execucao na porta 5432." -ForegroundColor Green
    }
}

if ($Mode -eq "db") {
    Start-PostgresIfStopped
    return
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
    Start-PostgresIfStopped
    Write-Host "Iniciando Backend na porta 8000..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; & '.\.venv\Scripts\uvicorn' app.main:app --reload --port 8000"
}

if ($Mode -eq "frontend" -or $Mode -eq "all") {
    Write-Host "Iniciando Frontend Vite..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; & 'C:\Users\fakef\.local\bin\fnm.exe' env --use-on-cd | Out-String | Invoke-Expression; npm run dev"
}

Write-Host "Ambiente pronto!" -ForegroundColor Cyan
