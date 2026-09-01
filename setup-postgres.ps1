$ErrorActionPreference = "Stop"
$pg_bin = "d:\Thiago\Projetos\Estetica\.pg_portable\pgsql\bin"
$pg_data = "d:\Thiago\Projetos\Estetica\.pg_portable\pgsql\data"
$pg_log = "d:\Thiago\Projetos\Estetica\.pg_portable\pgsql\logfile.log"

if (-not (Test-Path $pg_data)) {
    Write-Host "===> 1. Inicializando cluster de dados..." -ForegroundColor Cyan
    & "$pg_bin\initdb.exe" -D $pg_data -U postgres -A trust -E UTF8
}

Write-Host "===> 2. Iniciando PostgreSQL Server..." -ForegroundColor Cyan
& "$pg_bin\pg_ctl.exe" -D $pg_data -l $pg_log -o "-p 5432" start

Start-Sleep -Seconds 3

Write-Host "===> 3. Criando database estetica e configurando usuario estetica_app..." -ForegroundColor Cyan
try {
    & "$pg_bin\createdb.exe" -U postgres -p 5432 estetica
} catch {
    Write-Host "Database ja existe ou criado."
}

& "$pg_bin\psql.exe" -U postgres -p 5432 -d estetica -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'estetica_app') THEN CREATE ROLE estetica_app WITH LOGIN PASSWORD 'CHANGEME'; END IF; END \$\$; GRANT ALL PRIVILEGES ON DATABASE estetica TO estetica_app; GRANT ALL ON SCHEMA public TO estetica_app;"

Write-Host "===> 4. Aplicando migracoes Alembic..." -ForegroundColor Cyan
Set-Location "d:\Thiago\Projetos\Estetica\backend"
$env:Path = "C:\Users\fakef\.local\bin;$env:Path"
& uv run alembic upgrade head

Write-Host "===> 5. Testando endpoint de status do sistema..." -ForegroundColor Green
& uv run python -c "import urllib.request; resp = urllib.request.urlopen('http://127.0.0.1:8000/api/v1/system/status'); print('API RESPONSE:', resp.read().decode())"

Write-Host "===> BANCO DE DADOS CONFIGURADO E PRONTO COM SUCESSO!" -ForegroundColor Green
