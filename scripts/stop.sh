#!/bin/bash

set -e

echo "🛑 Stopping PM Backend..."

docker-compose down

echo "✅ PM Backend stopped"
echo ""
echo "To restart: ./scripts/start.sh"
