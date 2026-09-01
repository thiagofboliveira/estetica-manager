# Script para manter o túnel público do frontend sempre ativo com reconexão automática
Write-Host "Iniciando túnel público para http://localhost:5173..." -ForegroundColor Cyan

while ($true) {
    Write-Host "Conectando ao serveo.net..." -ForegroundColor Yellow
    ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -R 80:localhost:5173 serveo.net
    Write-Host "Conexão encerrada. Reconectando em 3 segundos..." -ForegroundColor Red
    Start-Sleep -Seconds 3
}
