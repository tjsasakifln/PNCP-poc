#!/bin/bash

##############################################################################
# E2E Test Runner Script for BidIQ Uniformes POC
#
# This script orchestrates the execution of end-to-end tests using Playwright
# Ensures proper environment setup and provides detailed test results
#
# Usage:
#   ./scripts/run-e2e-tests.sh [options]
#
# Options:
#   --headed         Run tests in headed mode (visible browser)
#   --debug          Run tests in debug mode with inspector
#   --ui             Run tests in UI mode (interactive)
#   --report         Generate and open HTML report after tests
#   --docker         Run tests against Docker Compose stack
#   --help           Show this help message
#
# Requirements:
#   - Node.js 18+ and npm
#   - Docker Desktop (if using --docker)
#   - Playwright installed (npm install in frontend/)
#
# Exit Codes:
#   0  - All tests passed
#   1  - Some tests failed
#   2  - Setup/environment error
#
# Author: AIOS Development Team
# Issue: #27 - Testes end-to-end
##############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
HEADED=false
DEBUG=false
UI=false
REPORT=false
USE_DOCKER=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --headed)
      HEADED=true
      shift
      ;;
    --debug)
      DEBUG=true
      shift
      ;;
    --ui)
      UI=true
      shift
      ;;
    --report)
      REPORT=true
      shift
      ;;
    --docker)
      USE_DOCKER=true
      shift
      ;;
    --help)
      grep '^#' "$0" | sed 's/^# //g' | sed 's/^#//g'
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Use --help for usage information"
      exit 2
      ;;
  esac
done

# Print banner
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   BidIQ Uniformes - E2E Test Runner${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Step 1: Environment validation
echo -e "${YELLOW}[1/5] Validating environment...${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
  echo -e "${RED}✗ Node.js not found${NC}"
  echo "Install Node.js 18+ from https://nodejs.org/"
  exit 2
fi

NODE_VERSION=$(node -v | sed 's/v//g' | cut -d '.' -f 1)
if [ "$NODE_VERSION" -lt 18 ]; then
  echo -e "${RED}✗ Node.js version must be >= 18 (found: $(node -v))${NC}"
  exit 2
fi

echo -e "${GREEN}✓ Node.js $(node -v)${NC}"

# Check npm
if ! command -v npm &> /dev/null; then
  echo -e "${RED}✗ npm not found${NC}"
  exit 2
fi

echo -e "${GREEN}✓ npm $(npm -v)${NC}"

# Check Docker (if --docker flag is used)
if [ "$USE_DOCKER" = true ]; then
  if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    echo "Install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 2
  fi

  if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker daemon not running${NC}"
    echo "Start Docker Desktop and try again"
    exit 2
  fi

  echo -e "${GREEN}✓ Docker $(docker --version | awk '{print $3}' | sed 's/,//g')${NC}"
fi

# Step 2: Install dependencies
echo ""
echo -e "${YELLOW}[2/5] Installing frontend dependencies...${NC}"

cd "$(dirname "$0")/../frontend" || exit 2

if [ ! -d "node_modules" ]; then
  echo "Running npm install..."
  npm install --silent
else
  echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi

# Install Playwright browsers if needed
if [ ! -d "$HOME/.cache/ms-playwright" ] && [ ! -d "$HOME/Library/Caches/ms-playwright" ]; then
  echo "Installing Playwright browsers..."
  npx playwright install chromium
else
  echo -e "${GREEN}✓ Playwright browsers installed${NC}"
fi

# Step 3: Start services
echo ""
echo -e "${YELLOW}[3/5] Starting services...${NC}"

if [ "$USE_DOCKER" = true ]; then
  echo "Starting Docker Compose stack..."
  cd "$(dirname "$0")/.." || exit 2
  docker-compose up -d

  # Wait for services to be healthy
  echo "Waiting for services to be ready..."
  sleep 10

  # Check backend health
  for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
      echo -e "${GREEN}✓ Backend ready${NC}"
      break
    fi

    if [ $i -eq 30 ]; then
      echo -e "${RED}✗ Backend failed to start${NC}"
      docker-compose logs backend
      exit 2
    fi

    sleep 2
  done

  # Check frontend
  for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null; then
      echo -e "${GREEN}✓ Frontend ready${NC}"
      break
    fi

    if [ $i -eq 30 ]; then
      echo -e "${RED}✗ Frontend failed to start${NC}"
      docker-compose logs frontend
      exit 2
    fi

    sleep 2
  done

else
  # Use Playwright's built-in webServer (configured in playwright.config.ts)
  echo -e "${GREEN}✓ Using Playwright webServer (automatic)${NC}"
fi

# Step 4: Run tests
echo ""
echo -e "${YELLOW}[4/5] Running E2E tests...${NC}"

cd "$(dirname "$0")/../frontend" || exit 2

# Build test command
TEST_CMD="npx playwright test"

if [ "$HEADED" = true ]; then
  TEST_CMD="$TEST_CMD --headed"
fi

if [ "$DEBUG" = true ]; then
  TEST_CMD="$TEST_CMD --debug"
fi

if [ "$UI" = true ]; then
  TEST_CMD="$TEST_CMD --ui"
fi

# Set environment variables
export FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
export BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

# Run tests
echo "Executing: $TEST_CMD"
echo ""

START_TIME=$(date +%s)

if $TEST_CMD; then
  TEST_RESULT=0
else
  TEST_RESULT=1
fi

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

# Step 5: Generate report
echo ""
echo -e "${YELLOW}[5/5] Test execution complete${NC}"

if [ "$REPORT" = true ] || [ $TEST_RESULT -ne 0 ]; then
  echo "Generating HTML report..."
  npx playwright show-report &
fi

# Print summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ $TEST_RESULT -eq 0 ]; then
  echo -e "${GREEN}✓ All tests passed in ${ELAPSED}s${NC}"
else
  echo -e "${RED}✗ Some tests failed (see report above)${NC}"
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Cleanup (if using Docker)
if [ "$USE_DOCKER" = true ]; then
  echo ""
  read -p "Stop Docker Compose stack? (y/N): " -n 1 -r
  echo

  if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$(dirname "$0")/.." || exit 2
    docker-compose down
    echo -e "${GREEN}✓ Services stopped${NC}"
  fi
fi

exit $TEST_RESULT
