#!/bin/bash

set -e

echo "🚀 Starting PM Backend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your OpenRouter API key"
fi

# Build and start containers
echo "📦 Building Docker image..."
docker-compose build

echo "🐳 Starting containers..."
docker-compose up -d

# Wait for service to be healthy
echo "⏳ Waiting for service to be healthy..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✅ Service is healthy!"
        echo ""
        echo "🎉 PM Backend is running!"
        echo "   API:    http://localhost:8000/api"
        echo "   Health: http://localhost:8000/api/health"
        echo ""
        echo "To view logs: docker-compose logs -f"
        echo "To stop:      ./scripts/stop.sh"
        exit 0
    fi
    echo "  Attempt $i/30..."
    sleep 1
done

echo "❌ Service failed to start. Check logs:"
docker-compose logs
exit 1
