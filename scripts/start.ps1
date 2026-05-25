#!/usr/bin/env pwsh

Write-Output "🚀 Starting PM Backend..."

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Output "⚠️  .env file not found. Creating from .env.example..."
    Copy-Item ".env.example" ".env"
    Write-Output "⚠️  Please update .env with your OpenRouter API key"
}

# Build and start containers
Write-Output "📦 Building Docker image..."
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Output "❌ Docker build failed"
    exit 1
}

Write-Output "🐳 Starting containers..."
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Output "❌ Docker-compose failed"
    exit 1
}

# Wait for service to be healthy
Write-Output "⏳ Waiting for service to be healthy..."
$maxAttempts = 30
for ($i = 1; $i -le $maxAttempts; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Output "✅ Service is healthy!"
            Write-Output ""
            Write-Output "🎉 PM Backend is running!"
            Write-Output "   API:    http://localhost:8000/api"
            Write-Output "   Health: http://localhost:8000/api/health"
            Write-Output ""
            Write-Output "To view logs: docker-compose logs -f"
            Write-Output "To stop:      .\scripts\stop.ps1"
            exit 0
        }
    }
    catch {
        # Service not ready yet
    }
    Write-Output "  Attempt $i/$maxAttempts..."
    Start-Sleep -Seconds 1
}

Write-Output "❌ Service failed to start. Check logs:"
docker-compose logs
exit 1
