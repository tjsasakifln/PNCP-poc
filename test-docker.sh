#!/bin/bash
# =============================================================================
# Docker Compose Test Script
# =============================================================================
# This script validates the Docker setup for BidIQ Uniformes POC
# Run this after Docker Desktop is running to verify the setup

set -e  # Exit on error

echo "🔍 Testing Docker Compose Configuration"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "   Please start Docker Desktop and try again"
    exit 1
fi
echo "✅ Docker is running"

# Check if docker-compose is available
if ! docker-compose --version > /dev/null 2>&1; then
    echo "❌ Error: docker-compose not found"
    exit 1
fi
echo "✅ docker-compose is available"

# Validate docker-compose.yml syntax
echo ""
echo "📋 Validating docker-compose.yml syntax..."
if docker-compose config --quiet; then
    echo "✅ docker-compose.yml syntax is valid"
else
    echo "❌ docker-compose.yml has syntax errors"
    exit 1
fi

# Check if .env exists
echo ""
echo "🔐 Checking environment configuration..."
if [ -f .env ]; then
    echo "✅ .env file exists"
else
    echo "⚠️  .env file not found (using .env.example defaults)"
    echo "   For full functionality, copy .env.example to .env and add OPENAI_API_KEY"
fi

# Build images
echo ""
echo "🏗️  Building Docker images..."
if docker-compose build; then
    echo "✅ Docker images built successfully"
else
    echo "❌ Failed to build Docker images"
    exit 1
fi

# Start services
echo ""
echo "🚀 Starting services..."
if docker-compose up -d; then
    echo "✅ Services started successfully"
else
    echo "❌ Failed to start services"
    exit 1
fi

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy (max 60s)..."
sleep 5

MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    BACKEND_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' bidiq-backend 2>/dev/null || echo "unknown")
    FRONTEND_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' bidiq-frontend 2>/dev/null || echo "unknown")

    if [ "$BACKEND_HEALTH" = "healthy" ] && [ "$FRONTEND_HEALTH" = "healthy" ]; then
        echo "✅ All services are healthy"
        break
    fi

    echo "   Backend: $BACKEND_HEALTH | Frontend: $FRONTEND_HEALTH (waited ${WAITED}s)"
    sleep 5
    WAITED=$((WAITED + 5))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "⚠️  Services did not become healthy within ${MAX_WAIT}s"
    echo "   Check logs with: docker-compose logs"
fi

# Test endpoints
echo ""
echo "🧪 Testing endpoints..."

# Test backend
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend is accessible at http://localhost:8000"
else
    echo "❌ Backend is not accessible at http://localhost:8000"
fi

if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ Backend Swagger UI is accessible at http://localhost:8000/docs"
else
    echo "❌ Backend Swagger UI is not accessible"
fi

# Test frontend
if curl -f http://localhost:3000/ > /dev/null 2>&1; then
    echo "✅ Frontend is accessible at http://localhost:3000"
else
    echo "❌ Frontend is not accessible at http://localhost:3000"
fi

# Show running containers
echo ""
echo "📊 Running containers:"
docker-compose ps

# Show logs
echo ""
echo "📋 Recent logs (last 20 lines):"
docker-compose logs --tail=20

echo ""
echo "========================================"
echo "✅ Docker setup verification complete!"
echo ""
echo "Useful commands:"
echo "  docker-compose logs -f           # Follow logs"
echo "  docker-compose logs -f backend   # Follow backend logs only"
echo "  docker-compose down              # Stop services"
echo "  docker-compose restart           # Restart services"
echo ""
echo "Access points:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API Docs: http://localhost:8000/docs"
echo "========================================"
