@echo off

echo 🛑 Stopping PM Backend...

docker-compose down
if errorlevel 1 (
    echo ❌ Docker-compose down failed
    exit /b 1
)

echo ✅ PM Backend stopped
echo.
echo To restart: .\scripts\start.bat
