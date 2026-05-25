@echo off
setlocal enabledelayedexpansion

echo 🚀 Starting PM Backend...

REM Check if .env exists
if not exist .env (
    echo ⚠️  .env file not found. Creating from .env.example...
    copy .env.example .env
    echo ⚠️  Please update .env with your OpenRouter API key
)

REM Build and start containers
echo 📦 Building Docker image...
docker-compose build
if errorlevel 1 (
    echo ❌ Docker build failed
    exit /b 1
)

echo 🐳 Starting containers...
docker-compose up -d
if errorlevel 1 (
    echo ❌ Docker-compose failed
    exit /b 1
)

REM Wait for service to be healthy
echo ⏳ Waiting for service to be healthy...
for /l %%i in (1,1,30) do (
    for /f %%A in ('powershell -Command "try { [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor [System.Net.SecurityProtocolType]::Tls12; (Invoke-WebRequest -Uri 'http://localhost:8000/api/health' -UseBasicParsing).StatusCode } catch { Write-Output 'error' }"') do set status=%%A
    if "!status!"=="200" (
        echo ✅ Service is healthy!
        echo.
        echo 🎉 PM Backend is running!
        echo    API:    http://localhost:8000/api
        echo    Health: http://localhost:8000/api/health
        echo.
        echo To view logs: docker-compose logs -f
        echo To stop:      .\scripts\stop.bat
        exit /b 0
    )
    echo   Attempt %%i/30...
    timeout /t 1 /nobreak >nul
)

echo ❌ Service failed to start. Check logs:
docker-compose logs
exit /b 1
