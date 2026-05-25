#!/usr/bin/env pwsh

Write-Output "🛑 Stopping PM Backend..."

docker-compose down
if ($LASTEXITCODE -ne 0) {
    Write-Output "❌ Docker-compose down failed"
    exit 1
}

Write-Output "✅ PM Backend stopped"
Write-Output ""
Write-Output "To restart: .\scripts\start.ps1"
