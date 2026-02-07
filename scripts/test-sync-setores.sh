#!/bin/bash

# Test script for sync-setores-fallback.js
# This script validates the sync script functionality

set -e

echo "======================================"
echo "Testing sync-setores-fallback.js"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Node.js is installed: $(node --version)${NC}"
echo ""

# Check if backend is running
echo "📡 Checking if backend is running..."
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

if curl -s -f -o /dev/null "$BACKEND_URL/health" 2>/dev/null; then
    echo -e "${GREEN}✅ Backend is running at $BACKEND_URL${NC}"
    BACKEND_RUNNING=true
else
    echo -e "${YELLOW}⚠️  Backend is not running at $BACKEND_URL${NC}"
    echo -e "${YELLOW}   Tests will be limited to script validation only${NC}"
    BACKEND_RUNNING=false
fi
echo ""

# Test 1: Dry run mode
echo "Test 1: Dry run mode (--dry-run)"
echo "────────────────────────────────────"

if [ "$BACKEND_RUNNING" = true ]; then
    if node scripts/sync-setores-fallback.js --dry-run --backend-url "$BACKEND_URL"; then
        echo -e "${GREEN}✅ Dry run completed successfully${NC}"
    else
        echo -e "${RED}❌ Dry run failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⏭️  Skipped (backend not running)${NC}"
fi
echo ""

# Test 2: Script exists and is executable
echo "Test 2: Script validation"
echo "────────────────────────────────────"

if [ -f "scripts/sync-setores-fallback.js" ]; then
    echo -e "${GREEN}✅ Script exists${NC}"
else
    echo -e "${RED}❌ Script not found${NC}"
    exit 1
fi

if [ -x "scripts/sync-setores-fallback.js" ]; then
    echo -e "${GREEN}✅ Script is executable${NC}"
else
    echo -e "${YELLOW}⚠️  Script is not executable (not critical on Windows)${NC}"
fi

# Check file size (should be > 1KB)
FILE_SIZE=$(wc -c < "scripts/sync-setores-fallback.js")
if [ "$FILE_SIZE" -gt 1000 ]; then
    echo -e "${GREEN}✅ Script has valid size: ${FILE_SIZE} bytes${NC}"
else
    echo -e "${RED}❌ Script seems too small: ${FILE_SIZE} bytes${NC}"
    exit 1
fi
echo ""

# Test 3: Documentation exists
echo "Test 3: Documentation"
echo "────────────────────────────────────"

if [ -f "scripts/README-sync-setores.md" ]; then
    echo -e "${GREEN}✅ Documentation exists${NC}"
    DOC_SIZE=$(wc -c < "scripts/README-sync-setores.md")
    echo -e "${GREEN}   Size: ${DOC_SIZE} bytes${NC}"
else
    echo -e "${RED}❌ Documentation not found${NC}"
    exit 1
fi
echo ""

# Test 4: Frontend file has SETORES_FALLBACK
echo "Test 4: Frontend implementation"
echo "────────────────────────────────────"

if grep -q "const SETORES_FALLBACK: Setor\[\]" frontend/app/buscar/page.tsx; then
    echo -e "${GREEN}✅ SETORES_FALLBACK constant exists${NC}"
else
    echo -e "${RED}❌ SETORES_FALLBACK constant not found${NC}"
    exit 1
fi

if grep -q "setoresUsingFallback" frontend/app/buscar/page.tsx; then
    echo -e "${GREEN}✅ Fallback state management exists${NC}"
else
    echo -e "${RED}❌ Fallback state not found${NC}"
    exit 1
fi

if grep -q "Usando lista offline de setores" frontend/app/buscar/page.tsx; then
    echo -e "${GREEN}✅ Warning banner exists${NC}"
else
    echo -e "${RED}❌ Warning banner not found${NC}"
    exit 1
fi

# Count sectors in fallback
SECTOR_COUNT=$(grep -o '{ id:' frontend/app/buscar/page.tsx | grep -A 2 'SETORES_FALLBACK' | wc -l)
if [ "$SECTOR_COUNT" -ge 10 ]; then
    echo -e "${GREEN}✅ Fallback list has sufficient sectors${NC}"
else
    echo -e "${YELLOW}⚠️  Fallback list has only a few sectors${NC}"
fi
echo ""

# Test 5: Retry logic
echo "Test 5: Retry logic implementation"
echo "────────────────────────────────────"

if grep -q "attempt < 2" frontend/app/buscar/page.tsx; then
    echo -e "${GREEN}✅ Retry logic with 3 attempts exists${NC}"
else
    echo -e "${RED}❌ Retry logic not found${NC}"
    exit 1
fi

if grep -q "Math.pow(2, attempt)" frontend/app/buscar/page.tsx; then
    echo -e "${GREEN}✅ Exponential backoff implemented${NC}"
else
    echo -e "${RED}❌ Exponential backoff not found${NC}"
    exit 1
fi
echo ""

# Summary
echo "======================================"
echo "Summary"
echo "======================================"
echo ""

if [ "$BACKEND_RUNNING" = true ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "You can now run the sync script:"
    echo "  node scripts/sync-setores-fallback.js"
else
    echo -e "${YELLOW}✅ All offline tests passed!${NC}"
    echo ""
    echo -e "${YELLOW}To test with backend:${NC}"
    echo "  1. Start backend: cd backend && uvicorn main:app --reload"
    echo "  2. Run: node scripts/sync-setores-fallback.js --dry-run"
fi
echo ""
