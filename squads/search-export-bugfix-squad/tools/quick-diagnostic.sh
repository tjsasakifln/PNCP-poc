#!/bin/bash
# Quick Diagnostic Script for Search & Export Bugs
# Run from project root: bash squads/search-export-bugfix-squad/tools/quick-diagnostic.sh

echo "🔍 SmartLic Bug Diagnostic - Quick Check"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Backend Health Check
echo "1️⃣ Backend Health Check"
echo "   Testing: http://localhost:8000/health"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
if [ "$HEALTH" = "200" ]; then
    echo -e "   ${GREEN}✅ Backend is running (HTTP 200)${NC}"
else
    echo -e "   ${RED}❌ Backend not running (HTTP $HEALTH)${NC}"
    echo -e "   ${YELLOW}   → Start backend: cd backend && uvicorn main:app --reload${NC}"
fi
echo ""

# 2. Export Route Check
echo "2️⃣ Export Route Accessibility Check"
echo "   Testing: POST /api/export/google-sheets"
EXPORT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  http://localhost:8000/api/export/google-sheets \
  -H "Content-Type: application/json" \
  -d '{"licitacoes":[],"title":"Test","mode":"create"}' 2>/dev/null)

if [ "$EXPORT_STATUS" = "401" ] || [ "$EXPORT_STATUS" = "422" ]; then
    echo -e "   ${GREEN}✅ Route exists (HTTP $EXPORT_STATUS - expected, needs auth)${NC}"
elif [ "$EXPORT_STATUS" = "404" ]; then
    echo -e "   ${RED}❌ Route NOT FOUND (HTTP 404) - BUG CONFIRMED!${NC}"
    echo -e "   ${YELLOW}   → Route is not registered or wrong prefix${NC}"
else
    echo -e "   ${YELLOW}⚠️  Unexpected status: HTTP $EXPORT_STATUS${NC}"
fi
echo ""

# 3. OpenAPI Spec Check
echo "3️⃣ OpenAPI Spec Check"
echo "   Checking if /api/export/google-sheets is in OpenAPI spec..."
HAS_EXPORT=$(curl -s http://localhost:8000/openapi.json 2>/dev/null | grep -o "api/export/google-sheets")
if [ -n "$HAS_EXPORT" ]; then
    echo -e "   ${GREEN}✅ Route found in OpenAPI spec${NC}"
else
    echo -e "   ${RED}❌ Route NOT in OpenAPI spec${NC}"
    echo -e "   ${YELLOW}   → Router may not be included in main.py${NC}"
fi
echo ""

# 4. CORS Preflight Check
echo "4️⃣ CORS Preflight Check"
echo "   Testing: OPTIONS /api/export/google-sheets"
CORS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
  http://localhost:8000/api/export/google-sheets \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" 2>/dev/null)

if [ "$CORS_STATUS" = "200" ]; then
    echo -e "   ${GREEN}✅ CORS preflight OK (HTTP 200)${NC}"
elif [ "$CORS_STATUS" = "404" ]; then
    echo -e "   ${RED}❌ CORS preflight failed (HTTP 404)${NC}"
    echo -e "   ${YELLOW}   → Check CORS middleware configuration${NC}"
else
    echo -e "   ${YELLOW}⚠️  CORS preflight status: HTTP $CORS_STATUS${NC}"
fi
echo ""

# 5. Backend Logs Check
echo "5️⃣ Recent Backend Logs (last 20 lines)"
echo "   Checking backend/logs/app.log for errors..."
if [ -f "backend/logs/app.log" ]; then
    echo ""
    tail -20 backend/logs/app.log | grep -i "error\|exception\|404" || echo "   (No errors found in last 20 lines)"
else
    echo -e "   ${YELLOW}⚠️  Log file not found: backend/logs/app.log${NC}"
fi
echo ""

# 6. pncp_client.py max_pages Check
echo "6️⃣ Search Pagination Limit Check"
echo "   Checking max_pages value in backend/pncp_client.py..."
MAX_PAGES=$(grep -n "max_pages.*=.*[0-9]" backend/pncp_client.py | head -1)
if echo "$MAX_PAGES" | grep -q "max_pages.*50"; then
    echo -e "   ${RED}❌ max_pages = 50 (TOO LOW!) - Line: $MAX_PAGES${NC}"
    echo -e "   ${YELLOW}   → Increase to 200-500 for comprehensive search${NC}"
elif echo "$MAX_PAGES" | grep -q "max_pages"; then
    echo -e "   ${GREEN}✅ max_pages value: $MAX_PAGES${NC}"
else
    echo -e "   ${YELLOW}⚠️  Could not detect max_pages value${NC}"
fi
echo ""

# Summary
echo "========================================" echo "📊 Diagnostic Summary"
echo "========================================"
echo ""

if [ "$HEALTH" = "200" ] && ([ "$EXPORT_STATUS" = "401" ] || [ "$EXPORT_STATUS" = "422" ]); then
    echo -e "${GREEN}✅ EXPORT BUG: Likely FIXED or not reproducible${NC}"
    echo "   - Backend is healthy"
    echo "   - Route is accessible"
else
    echo -e "${RED}❌ EXPORT BUG: CONFIRMED${NC}"
    [ "$HEALTH" != "200" ] && echo "   - Backend not running"
    [ "$EXPORT_STATUS" = "404" ] && echo "   - Route returns 404"
fi

echo ""

if echo "$MAX_PAGES" | grep -q "max_pages.*50"; then
    echo -e "${RED}❌ SEARCH BUG: LIKELY CAUSE FOUND${NC}"
    echo "   - max_pages = 50 is too low"
    echo "   - Limits search to 1000 records per UF+modalidade"
else
    echo -e "${GREEN}✅ SEARCH BUG: max_pages seems OK${NC}"
fi

echo ""
echo "========================================" echo "🔧 Recommended Actions"
echo "========================================"
echo ""

# Export bug recommendations
if [ "$EXPORT_STATUS" = "404" ]; then
    echo "EXPORT BUG:"
    echo "  1. Verify backend is running: uvicorn main:app --reload"
    echo "  2. Check main.py includes export_sheets_router"
    echo "  3. Visit http://localhost:8000/docs to verify route exists"
    echo ""
fi

# Search bug recommendations
if echo "$MAX_PAGES" | grep -q "max_pages.*50"; then
    echo "SEARCH BUG:"
    echo "  1. Edit backend/pncp_client.py line ~461"
    echo "  2. Change: max_pages: int = 50"
    echo "  3. To:     max_pages: int = 500"
    echo "  4. Add warning when max_pages is reached"
    echo ""
fi

echo "For detailed diagnostic steps, see:"
echo "  - squads/search-export-bugfix-squad/tasks/diagnose-search-bug.md"
echo "  - squads/search-export-bugfix-squad/tasks/diagnose-export-bug.md"
echo ""
