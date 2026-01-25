#!/bin/bash
# =============================================================================
# Integration Verification Script
# =============================================================================
# Tests basic connectivity between frontend and backend services
# Usage: ./scripts/verify-integration.sh
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed
# =============================================================================

set -e  # Exit on first error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
PASS=0
FAIL=0

echo "=================================================="
echo "  BidIQ Uniformes - Integration Verification"
echo "=================================================="
echo ""

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL++))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# -----------------------------------------------------------------------------
# Pre-flight Checks
# -----------------------------------------------------------------------------

echo "Pre-flight Checks:"
echo "--------------------------------------------------"

# Check Docker is running
if docker info > /dev/null 2>&1; then
    pass "Docker daemon is running"
else
    fail "Docker daemon is not running"
    echo ""
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Check .env file exists
if [ -f ".env" ]; then
    pass ".env file exists"

    # Check for OPENAI_API_KEY
    if grep -q "^OPENAI_API_KEY=sk-" .env; then
        pass "OPENAI_API_KEY is configured"
    else
        warn "OPENAI_API_KEY not found or invalid in .env"
        echo "   This may cause LLM summary generation to fail."
    fi
else
    fail ".env file not found"
    echo ""
    echo "Create .env file: cp .env.example .env"
    echo "Then add your OPENAI_API_KEY"
    exit 1
fi

echo ""

# -----------------------------------------------------------------------------
# Service Health Checks
# -----------------------------------------------------------------------------

echo "Service Health Checks:"
echo "--------------------------------------------------"

# Check if services are running
BACKEND_RUNNING=$(docker-compose ps -q backend 2>/dev/null)
FRONTEND_RUNNING=$(docker-compose ps -q frontend 2>/dev/null)

if [ -z "$BACKEND_RUNNING" ]; then
    fail "Backend container is not running"
    echo ""
    echo "Start services with: docker-compose up -d"
    exit 1
else
    pass "Backend container is running"
fi

if [ -z "$FRONTEND_RUNNING" ]; then
    fail "Frontend container is not running"
    echo ""
    echo "Start services with: docker-compose up -d"
    exit 1
else
    pass "Frontend container is running"
fi

echo ""

# -----------------------------------------------------------------------------
# HTTP Connectivity Tests
# -----------------------------------------------------------------------------

echo "HTTP Connectivity Tests:"
echo "--------------------------------------------------"

# Test backend health endpoint
BACKEND_URL="http://localhost:8000"
if curl -s -f "$BACKEND_URL/health" > /dev/null; then
    pass "Backend health endpoint responding (GET /health)"
else
    fail "Backend health endpoint not responding"
    echo "   Expected: HTTP 200 from $BACKEND_URL/health"
fi

# Test backend root endpoint
if curl -s -f "$BACKEND_URL/" > /dev/null; then
    pass "Backend root endpoint responding (GET /)"
else
    fail "Backend root endpoint not responding"
fi

# Test backend OpenAPI docs
if curl -s -f "$BACKEND_URL/docs" > /dev/null; then
    pass "Backend API docs responding (GET /docs)"
else
    warn "Backend API docs not responding"
fi

# Test frontend root
FRONTEND_URL="http://localhost:3000"
if curl -s -f "$FRONTEND_URL/" > /dev/null; then
    pass "Frontend root endpoint responding (GET /)"
else
    fail "Frontend root endpoint not responding"
    echo "   Expected: HTTP 200 from $FRONTEND_URL/"
fi

echo ""

# -----------------------------------------------------------------------------
# CORS Verification
# -----------------------------------------------------------------------------

echo "CORS Configuration:"
echo "--------------------------------------------------"

# Test CORS headers from backend
CORS_HEADER=$(curl -s -I -X OPTIONS "$BACKEND_URL/" | grep -i "access-control-allow-origin" || echo "")

if [ -n "$CORS_HEADER" ]; then
    pass "CORS headers present in backend response"
    echo "   $CORS_HEADER" | sed 's/^/   /'
else
    fail "CORS headers not found in backend response"
    echo "   Frontend may encounter CORS errors"
fi

echo ""

# -----------------------------------------------------------------------------
# Docker Network Verification
# -----------------------------------------------------------------------------

echo "Docker Network:"
echo "--------------------------------------------------"

# Check if bidiq-network exists
if docker network inspect bidiq-network > /dev/null 2>&1; then
    pass "Docker network 'bidiq-network' exists"

    # Check if both containers are on the network
    BACKEND_ON_NET=$(docker network inspect bidiq-network -f '{{range .Containers}}{{.Name}} {{end}}' | grep -o "bidiq-backend" || echo "")
    FRONTEND_ON_NET=$(docker network inspect bidiq-network -f '{{range .Containers}}{{.Name}} {{end}}' | grep -o "bidiq-frontend" || echo "")

    if [ -n "$BACKEND_ON_NET" ]; then
        pass "Backend container connected to bidiq-network"
    else
        fail "Backend container not on bidiq-network"
    fi

    if [ -n "$FRONTEND_ON_NET" ]; then
        pass "Frontend container connected to bidiq-network"
    else
        fail "Frontend container not on bidiq-network"
    fi
else
    fail "Docker network 'bidiq-network' not found"
fi

echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

echo "=================================================="
echo "  Summary"
echo "=================================================="
echo ""
echo -e "Tests Passed: ${GREEN}$PASS${NC}"
echo -e "Tests Failed: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All integration checks passed!${NC}"
    echo ""
    echo "Services are ready:"
    echo "  • Frontend: http://localhost:3000"
    echo "  • Backend:  http://localhost:8000"
    echo "  • API Docs: http://localhost:8000/docs"
    echo ""
    echo "Next steps:"
    echo "  1. Open http://localhost:3000 in your browser"
    echo "  2. Follow the integration guide: docs/INTEGRATION.md"
    exit 0
else
    echo -e "${RED}✗ Integration checks failed!${NC}"
    echo ""
    echo "Please fix the issues above and try again."
    echo ""
    echo "Common solutions:"
    echo "  • Start services: docker-compose up -d"
    echo "  • Check logs: docker-compose logs -f"
    echo "  • Rebuild: docker-compose build --no-cache"
    echo "  • See troubleshooting: docs/INTEGRATION.md#troubleshooting"
    exit 1
fi
